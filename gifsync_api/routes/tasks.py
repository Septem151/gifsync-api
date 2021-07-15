"""Resource route definitions for /tasks"""
from http import HTTPStatus

from flask import Blueprint

from ..extensions import rq_queue
from ..representations import Task

tasks_blueprint = Blueprint("tasks", __name__, url_prefix="/tasks")


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
