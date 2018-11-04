# -*- coding: utf-8 -*-

import os

import click

from . import __version__
from . import configuration as conf
from .operators.python_operator import PythonOperator
from .tasks import split, extract
from .utils.database import initialize_database, reset_database
from .www.app import create_app


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@click.group()
@click.version_option(version=__version__)
def cli(*args, **kwargs):
    pass


@cli.command('initdb')
def initdb(*args, **kwargs):
    initialize_database()


@cli.command('resetdb')
def resetdb(*args, **kwargs):
    click.confirm(
        "This will drop existing tables if they exist. Proceed?", abort=True)

    reset_database()
    initialize_database()


@cli.command('webserver')
def webserver(*args, **kwargs):
    app = create_app(conf)
    app.run(use_reloader=False)


@cli.command('worker')
def worker(*args, **kwargs):
    from celery.bin import worker
    from .executors.celery_executor import app as celery_app


    worker = worker.worker(app=celery_app)
    options = {
        'concurrency': int(conf.get('celery', 'WORKER_CONCURRENCY')),
        'loglevel': conf.get('core', 'LOGGING_LEVEL')
    }
    worker.run(**options)


@cli.command('run')
@click.option('-t', '--task')
@click.option('-id', '--uuid')
def run(*args, **kwargs):
    task_name = kwargs['task']
    task_id = kwargs['uuid']

    task_bag = {
        'split': split,
        'extract': extract
    }
    python_callable = task_bag[task_name]
    task = PythonOperator(python_callable, op_args=[task_id])
    task.execute()
