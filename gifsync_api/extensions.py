"""
Extensions for the GifSync API, such as CORS support, JWT management,
Database interaction, and Task scheduling.
"""
import typing as t

from flask_cors import CORS
from flask_pyjwt import AuthManager
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from rq import Queue
from rq.command import send_stop_job_command
from rq.job import Job


class RedisClient:
    """Wrapper for a Redis client.

    Args:
        redis_url (:obj:`str`, optional): The Redis connection string.
            Ex: "redis://localhost:6379/0". Defaults to None.
    """

    def __init__(self, redis_url: t.Optional[str] = None) -> None:

        self._client: t.Optional[Redis] = None
        if redis_url:
            self.init_redis(redis_url)

    def init_redis(self, redis_url: str) -> None:
        """Initializes the Redis client with the given connection string.

        Args:
            redis_url (:obj:`str`): The Redis connection string.
                Ex: "redis://localhost:6379/0"
        """
        self._client = Redis.from_url(redis_url)

    @property
    def client(self) -> Redis:
        """Returns the Redis client this wrapper contains.

        Raises:
            :obj:`AttributeError`: If the Redis client hasn't been initialized with a
                connection string.

        Returns:
            :obj:`~redis.Redis`: The Redis object.
        """
        if not self._client:
            raise AttributeError("Redis Client was not assigned yet!")
        return self._client


class RQ:
    """Wrapper for a Redis Queue.

    The Queue will have the name "GifSync".

    Args:
        client (:obj:`~redis.Redis`, optional): The Redis client. Defaults to None.
    """

    def __init__(self, client: t.Optional[Redis] = None) -> None:
        self._queue: t.Optional[Queue] = None
        if client:
            self.init_queue(client)

    def init_queue(self, client: Redis) -> None:
        """Initializes the Redis Queue with the given Redis client and a queue name
        of "GifSync".

        Args:
            client (:obj:`~redis.Redis`): The Redis client.
        """
        self._queue = Queue("GifSync", connection=client)

    @property
    def queue(self) -> Queue:
        """Returns the Redis Queue this wrapper contains.

        Raises:
            :obj:`AttributeError`: If the Redis Queue hasn't been initialized with a
                Redis client.

        Returns:
            :obj:`~rq.Queue`: The Redis Queue object.
        """
        if not self._queue:
            raise AttributeError("RQ Queue was not assigned yet!")
        return self._queue

    def add_job(self, job: t.Callable, *args, **kwargs) -> Job:
        """Enqueues a job to the Redis Queue this wrapper contains.

        Args:
            job (:obj:`Callable`): The job function.
            *args: Any arguments to pass to the job function.
            **kwargs: Any keyword arguments to pass to the job function.

        Raises:
            :obj:`AttributeError`: If the Redis Queue hasn't been initialized with a
                Redis client.

        Returns:
            :obj:`~rq.job.Job`: The enqueued job.
        """
        queued_job: Job = self.queue.enqueue(job, *args, **kwargs)
        return queued_job

    def get_job(self, job_id: str) -> t.Optional[Job]:
        """Returns a job from the Redis Queue this wrapper contains.

        Args:
            job_id (:obj:`str`): Id of the job.

        Raises:
            :obj:`AttributeError`: If the Redis Queue hasn't been initialized with a
                Redis client.

        Returns:
            :obj:`~rq.job.Job` | ``None``: The job from the Redis Queue this wrapper
                contains, or None if a job with the given id does not exist.
        """
        job: t.Optional[Job] = self.queue.fetch_job(job_id)
        return job

    def get_queued_jobs(self) -> t.List[str]:
        """Returns a list of jobs that are waiting to be executed by the Redis Queue
        this wrapper contains.

        Raises:
            :obj:`AttributeError`: If the Redis Queue hasn't been initialized with a
                Redis client.

        Returns:
            list(str): The queued jobs from the Redis Queue this wrapper contains.
        """
        jobs: t.List[str] = self.queue.get_job_ids()
        return jobs

    def get_started_jobs(self) -> t.List[str]:
        """Returns a list of jobs that are currently being executed by the Redis Queue
        this wrapper contains.

        Raises:
            :obj:`AttributeError`: If the Redis Queue hasn't been initialized with a
                Redis client.

        Returns:
            list(str): The currently executing jobs from the Redis Queue this
                wrapper contains.
        """
        jobs: t.List[str] = self.queue.started_job_registry.get_job_ids()
        return jobs

    def cancel_job(self, job_id: str) -> bool:
        """Cancels a job that is either currently executing or pending execution on the
        Redis Queue this wrapper contains.

        Args:
            job_id (:obj:`str`): Id of the job.

        Raises:
            :obj:`AttributeError`: If the Redis Queue hasn't been initialized with a
                Redis client.

        Returns:
            :obj:`bool`: Whether a job with the given id was found in the Redis Queue
                this wrapper contains.
        """
        job_found = False
        if job_id in self.get_started_jobs():
            send_stop_job_command(self.queue.connection, job_id)
            job_found = True
        elif job_id in self.get_queued_jobs():
            self.queue.remove(job_id)
            job_found = True

        return job_found


auth_manager = AuthManager()
cors = CORS()
db = SQLAlchemy()
redis_client = RedisClient()
rq_queue = RQ()
