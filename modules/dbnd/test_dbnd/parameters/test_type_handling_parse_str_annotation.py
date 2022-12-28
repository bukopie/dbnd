# © Copyright Databand.ai, an IBM Company 2022
import pandas as pd

from targets.values import (
    DictValueType,
    IntValueType,
    ListValueType,
    StrValueType,
    TargetPathLibValueType,
    ValueTypeLoader,
    get_types_registry,
)
from targets.values.structure import _StructureValueType


class TestTypeHandlingParseStrAnnotation(object):
    def test_dict_simple_parse(self):
        r = get_types_registry()
        actual = r.get_value_type_of_type_str("Dict[str,str]")
        assert isinstance(actual, DictValueType)
        assert isinstance(actual.sub_value_type, StrValueType)

    def test_dict_Path_parse(self):
        r = get_types_registry()
        actual = r.get_value_type_of_type_str("Dict[str,Path]")
        assert isinstance(actual, DictValueType)
        assert isinstance(actual.sub_value_type, TargetPathLibValueType)

    def test_List_parse(self):
        r = get_types_registry()
        actual = r.get_value_type_of_type_str("List")
        assert isinstance(actual, ListValueType)
        assert actual.sub_value_type is None

    def test_List_df_parse(self):
        r = get_types_registry()
        actual = r.get_value_type_of_type_str("List[pd.DataFrame]")
        assert isinstance(actual, _StructureValueType)
        assert isinstance(actual.sub_value_type, ValueTypeLoader)
        assert actual.sub_value_type.type_str == "pandas.core.frame.DataFrame"

    def test_dict_nested_parse_int(self):
        r = get_types_registry()
        actual = r.get_value_type_of_type_str("Dict[str, Dict[ str,int]]")
        assert isinstance(actual, DictValueType)
        assert isinstance(actual.sub_value_type, DictValueType)
        assert isinstance(actual.sub_value_type.sub_value_type, IntValueType)

    def test_dict_nested_parse_df(self):
        r = get_types_registry()
        actual = r.get_value_type_of_type_str("Dict[str, Dict[ str, pd.DataFrame]]")
        assert isinstance(actual, DictValueType)
        assert isinstance(actual.sub_value_type, ValueTypeLoader)
        sub_value_type = actual.sub_value_type.load_value_type()
        assert sub_value_type.sub_value_type.type == pd.DataFrame
