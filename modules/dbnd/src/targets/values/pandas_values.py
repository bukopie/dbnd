from __future__ import absolute_import

import logging
import os

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import six

from pandas.core.dtypes.common import is_bool_dtype, is_numeric_dtype, is_string_dtype
from pandas.core.util.hashing import hash_pandas_object

from dbnd._core.errors import friendly_error
from dbnd._vendor import fast_hasher
from targets.target_config import FileFormat
from targets.value_meta import ValueMeta, ValueMetaConf
from targets.values.builtins_values import DataValueType
from targets.values.structure import DictValueType
from targets.values.value_type import _isinstances


logger = logging.getLogger(__name__)


class DataFrameValueType(DataValueType):
    type = pd.DataFrame
    type_str = "DataFrame"
    support_merge = True

    config_name = "pandas_dataframe"

    def to_signature(self, x):
        shape = "[%s]" % (",".join(map(str, x.shape)))
        return "%s:%s" % (shape, fast_hasher.hash(x))

    def to_preview(self, df, preview_size):  # type: (pd.DataFrame, int) -> str
        return df.to_string(index=False, max_rows=20, max_cols=1000)[:preview_size]

    def get_value_meta(self, value, meta_conf):
        # type: (pd.DataFrame, ValueMetaConf) -> ValueMeta
        data_schema = {}
        if meta_conf.log_schema:
            data_schema.update(
                {
                    "type": self.type_str,
                    "columns": list(value.columns),
                    "shape": value.shape,
                    "dtypes": {col: str(type_) for col, type_ in value.dtypes.items()},
                }
            )

        if meta_conf.log_size:
            data_schema["size"] = int(value.size)

        value_preview, data_hash = None, None
        if meta_conf.log_preview:
            value_preview = self.to_preview(
                value, preview_size=meta_conf.get_preview_size()
            )
            data_hash = fast_hasher.hash(hash_pandas_object(value, index=True).values)

        df_stats, histograms = None, None
        if meta_conf.log_df_hist:
            df_stats, histograms = self.get_histograms(value)

        return ValueMeta(
            value_preview=value_preview,
            data_dimensions=value.shape,
            data_schema=data_schema,
            data_hash=data_hash,
            descriptive_stats=df_stats,
            histograms=histograms,
        )

    @classmethod
    def get_histograms(cls, df):
        # type: (pd.DataFrame) -> Tuple[Dict[Dict[str, Any]], Dict[str, Tuple]]
        histograms = df.apply(cls._calculate_histograms, args=(df.describe(), df))
        hist_dict, stats_dict = {}, {}
        for column, hist_stats in histograms.to_dict().items():
            if hist_stats:
                hist, bins, stats = hist_stats
                hist_dict[column] = (hist, bins)
                stats_dict[column] = stats
        return stats_dict, hist_dict

    @staticmethod
    def _calculate_histograms(df_column, df_stats, df):
        # type: (pd.Series, pd.Series, pd.DataFrame) -> Optional[Tuple[List, List, Dict]]
        column_stats = df_stats.get(df_column.name, None)  # type: pd.Series
        if column_stats is None:
            return
        column_stats["null-count"] = np.count_nonzero(pd.isnull(df_column))
        column_stats["non-null"] = df_column.size - column_stats["null-count"]
        column_stats["distinct"] = len(df_column.unique())

        try:
            # TODO: check efficiency
            df_type = df[df_column.name]
            column_stats["type"] = df_type.dtype.name
            if is_bool_dtype(df_type) or is_string_dtype(df_type):
                column_stats["count"] = int(column_stats["count"])
                column_stats["freq"] = int(column_stats["freq"])

                hist = df_column.value_counts()
                if column_stats["distinct"] > 50:
                    hist, tail = hist[:49], hist[49:]
                    tail_sum = pd.Series([tail.sum()], index=["_others"])
                    hist = hist.append(tail_sum)
                bin_edges = hist.index

            # For some reason is_numeric_dtype(df_column) returns different result
            elif is_numeric_dtype(df_type):
                bins = int(min(20, max(column_stats["distinct"] - 1, 1)))
                hist, bin_edges = np.histogram(
                    df_column, bins=bins
                )  # type: np.array, np.array
            else:
                return

            return hist.tolist(), bin_edges.tolist(), column_stats.to_dict()
        except Exception as ex:
            logger.exception(
                "log_histogram: Something went wrong for column '%s'", df_column.name
            )

    def merge_values(self, *values, **kwargs):
        # Concatenate all data into one DataFrame
        # We don't want list to be stored in memory
        # however, concat does list() on the iterator as one of the first things

        # # right now we can base our decision on:
        # # if our parts have RangeIndex (_default_index())
        # # let ignore it and have new index

        # we know that some formats can't have an index,
        # but let just base our decision on RangeIndex
        # file_format = kwargs.get("file_format", None)
        # storage_format_support_index = False
        # if file_format:
        #     storage_format_support_index = file_format in PANDAS_CACHE_SUPPORTED_FORMATS
        # else:
        #     all_formats = {t.file_format for t in targets}
        #     storage_format_support_index = all(f in PANDAS_CACHE_SUPPORTED_FORMATS for f in all_formats)

        meaningful_index = kwargs.get("set_index")
        # if we don't have index based on some data column
        if not meaningful_index:
            from targets.marshalling.pandas import _is_default_index

            meaningful_index = all(not _is_default_index(df) for df in values)

        return pd.concat(
            values, verify_integrity=True, ignore_index=not meaningful_index
        )


class PandasSeriesValueType(DataFrameValueType):
    type = pd.Series
    type_str = "Series"
    support_merge = False

    config_name = "pandas_series"


class DataFramesDictValueType(DictValueType):
    type = Dict[str, pd.DataFrame]
    type_str = "Dict[str,DataFrame]"
    type_str_extras = ("DataFrameDict", "Dict[str,pd.DataFrame]")
    config_name = "pandas_dataframe"
    sub_value_type = DataFrameValueType()

    def is_handler_of_type(self, type_):
        return type_ == self.type

    def is_type_of(self, value):
        if value is None:
            return False
        if not isinstance(value, dict):
            return False
        return value and _isinstances(value.values(), pd.DataFrame)

    def load_from_target(self, target, **kwargs):
        if target.config.format == FileFormat.hdf5:
            return target.load(value_type=Dict[str, pd.DataFrame])

        from targets import DirTarget

        if isinstance(target, DirTarget):

            result = {}
            for p in target.list_partitions():
                p_name = "/" + os.path.splitext(os.path.basename(p.path))[0]
                result[p_name] = p.load(value_type=pd.DataFrame, **kwargs)
            return result
        else:
            return target.load(value_type=Dict, **kwargs)

    def save_to_target(self, target, value, **kwargs):
        from targets.dir_target import DirTarget

        if not isinstance(value, dict):
            raise friendly_error.targets.data_frame_dict_value_should_be_dict(
                target, value
            )
        if isinstance(target, DirTarget):
            for key, partition_value in six.iteritems(value):
                target.partition(key).dump(
                    value=partition_value, value_type=pd.DataFrame
                )
            target.mark_success()
        else:
            # if target.config.format == FileFormat.hdf5:
            target.dump(value=value, value_type=self)

    def __str__(self):
        return "Dict[Any,DataFrame]"
