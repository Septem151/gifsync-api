"""Resource route definitions for /tasks"""
import typing as t
from http import HTTPStatus

from flask import Blueprint, request
from flask_pyjwt import require_token

from ..extensions import rq_queue
from ..representations import Task

tasks_blueprint = Blueprint("tasks", __name__, url_prefix="/tasks")


@tasks_blueprint.route("", methods=["GET"])
@require_token(scope={"admin": True})
def get_tasks_route():
    """GET /tasks

    Gets all tasks. Must be an admin.
    Can specify via request params whether you want just
    queued tasks or just started tasks.

    Example requests:

    * GET /tasks?query=queued

        * Only gets queued tasks

    * GET /tasks?query=started

        * Only get started tasks

    * GET /tasks?query=queued,started
    * GET /tasks

        * Gets both queued and started tasks

    """
    query = ["queued", "started"]
    query_args: t.Optional[str] = request.args.get("query")
    if query_args:
        query = query_args.lower().split(",")
    resp_json: dict = {}
    if "queued" in query:
        resp_json["queued"] = rq_queue.get_queued_jobs()
    if "started" in query:
        resp_json["started"] = rq_queue.get_started_jobs()
    if len(resp_json) == 0:
        return {
            "error": "query params must be of 'queued' or 'started'"
        }, HTTPStatus.BAD_REQUEST
    return resp_json, HTTPStatus.OK


@tasks_blueprint.route("", methods=["DELETE"])
@require_token(scope={"admin": True})
def delete_tasks_route():
    """DELETE /tasks

    Deletes all queued and/or started tasks. Must be an admin.
    Can specify via request params whether you want just
    queued tasks or just started tasks.

    Example requests:

    * DELETE /tasks?query=queued

        * Only deletes queued tasks

    * DELETE /tasks?query=started

        * Only deletes started tasks

    * DELETE /tasks?query=queued,started
    * DELETE /tasks

        * Deletes both queued and started tasks

    """
    query = ["queued", "started"]
    query_args: t.Optional[str] = request.args.get("query")
    jobs = []
    if query_args:
        query = query_args.lower().split(",")
    if "queued" in query:
        jobs += rq_queue.get_queued_jobs()
    if "started" in query:
        jobs += rq_queue.get_started_jobs()
    for job in jobs:
        rq_queue.cancel_job(job)
    return "", HTTPStatus.NO_CONTENT


@tasks_blueprint.route("/<string:task_id>", methods=["GET"])
def get_task_route(task_id: str):
    """GET /task/<task_id>

    Gets the completion status of a task.

    Args:
        task_id (:obj:`str`): Id of the task to get.
    """
    task = rq_queue.get_job(task_id)
    if not task:
        return {f"task with the id {task_id} not found"}, HTTPStatus.NOT_FOUND
    status = task.get_status()
    completed = status.lower() == "finished"
    if (
        status.lower() == "failed"
        or status.lower() == "stopped"
        or (status.lower() == "finished" and task.result is False)
    ):
        resp_code = HTTPStatus.INTERNAL_SERVER_ERROR
    else:
        resp_code = HTTPStatus.OK
    task_res = Task(task_id, completed)
    return task_res.to_json(), resp_code
