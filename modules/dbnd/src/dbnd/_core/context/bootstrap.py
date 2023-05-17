# © Copyright Databand.ai, an IBM Company 2022

import logging
import os

import dbnd

from dbnd._core.configuration.environ_config import _env_banner, get_dbnd_project_config


logger = logging.getLogger(__name__)

_dbnd_bootstrap_status = None


def dbnd_bootstrap():
    """Runs dbnd bootstrapping."""
    global _dbnd_bootstrap_status
    if _dbnd_bootstrap_status is not None:
        return
    try:
        _dbnd_bootstrap_status = "loading"
        # this will also initialize env if it's not initialized
        project_config = get_dbnd_project_config()

        if not project_config.quiet_mode:
            logger.info("Starting Databand %s!\n%s", dbnd.__version__, _env_banner())
            dbnd_run_info_source_version = os.environ.get(
                "DBND__RUN_INFO__SOURCE_VERSION"
            )
            if dbnd_run_info_source_version:
                logger.info("revision: %s", dbnd_run_info_source_version)
        from dbnd import dbnd_config

        dbnd_config.load_system_configs()

        from dbnd.providers.spark.dbnd_spark_init import try_load_spark_env

        try_load_spark_env()

        if project_config.is_sigquit_handler_on:
            from dbnd._core.utils.basics.signal_utils import (
                register_sigquit_stack_dump_handler,
            )

            register_sigquit_stack_dump_handler()

        _dbnd_bootstrap_status = "loaded"
    except Exception as ex:
        _dbnd_bootstrap_status = "error: %s" % str(ex)
        raise ex
