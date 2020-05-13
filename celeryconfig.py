# -*- codding: utf-8 -*-

from datetime import timedelta


BROKER_URL = 'redis://10.10.19.6:6379/1'

CELERY_RESULT_BACKEND = 'redis://10.10.19.6:6379/2'


CELERY_TIMEZONE = 'Asia/Shanghai'

# 导入指定的任务模块
CELERY_IMPORTS = (
    'albumy.task1',
)

CELERYBEAT_SCHEDULE = {
    'task1': {
        'task': 'albumy.task1.add',
        'schedule': timedelta(seconds=10),
        'args': (2, 8)
    }
}
