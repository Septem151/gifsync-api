"""
Extensions for the GifSync API, such as CORS support, JWT management,
Database interaction, and Task scheduling.
"""
import secrets
import subprocess
import typing as t

import boto3
from botocore.exceptions import ClientError
from fakeredis import FakeStrictRedis
from flask_cors import CORS
from flask_migrate import Migrate
from flask_pyjwt import AuthManager
from flask_sqlalchemy import SQLAlchemy
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.service_resource import Bucket, S3ServiceResource
from mypy_boto3_s3.type_defs import DeleteObjectsOutputTypeDef, GetObjectOutputTypeDef
from redis import Redis
from rq import Queue
from rq.command import send_stop_job_command
from rq.job import Job


class RedisClient:
    """Wrapper for a Redis client.

    Args:
        redis_url (:obj:`str`, optional): The Redis connection string.
            Ex: "redis://localhost:6379/0". Defaults to None.
        test_mode (:obj:`bool`, optional): Whether the redis client should be
            in test mode. Defaults to False.
    """

    def __init__(
        self, redis_url: t.Optional[str] = None, test_mode: bool = False
    ) -> None:

        self._client: t.Optional[Redis] = None
        if redis_url:
            self.init_redis(redis_url, test_mode)

    def init_redis(self, redis_url: str, test_mode: bool = False) -> None:
        """Initializes the Redis client with the given connection string.

        Args:
            redis_url (:obj:`str`): The Redis connection string.
                Ex: "redis://localhost:6379/0"
            test_mode (:obj:`bool`, optional): Whether the redis client should
                be in test mode. Defaults to False.
        """
        if test_mode:
            self._client = FakeStrictRedis()
        else:
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
        test_mode (:obj:`bool`, optional): Whether the queue should be
            in test mode. Defaults to False.
    """

    def __init__(
        self, client: t.Optional[Redis] = None, test_mode: bool = False
    ) -> None:
        self._queue: t.Optional[Queue] = None
        self._test_mode: bool = test_mode
        if client:
            self.init_queue(client, test_mode)

    def init_queue(self, client: Redis, test_mode: bool = False) -> None:
        """Initializes the Redis Queue with the given Redis client and a queue name
        of "GifSync".

        Args:
            client (:obj:`~redis.Redis`): The Redis client.
            test_mode (:obj:`bool`, optional): Whether the queue should be
                in test mode. Defaults to False.
        """
        if test_mode:
            self._queue = Queue("GifSync", is_async=False, connection=client)
        else:
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

    @property
    def test_mode(self) -> bool:
        """Returns whether this Redis Queue is in test mode.

        Returns:
            :obj:`bool`: True if test mode enabled, otherwise False.
        """
        return self._test_mode

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


class S3:
    """Wrapper for an S3 client.

    The S3 client is in the region "us-east-1" by default.

    Args:
        access_key (:obj:`str`, optional): The AWS Access Key. Defaults to None.
        secret_key (:obj:`str`, optional): The AWS Secret Key. Defaults to None.
        region_name (:obj:`str`): The AWS Region. Defaults to "us-east-1".
        bucket_name (:obj:`str`, optional): The S3 Bucket name. Defaults to None.
    """

    def __init__(
        self,
        access_key: t.Optional[str] = None,
        secret_key: t.Optional[str] = None,
        region_name: str = "us-east-1",
        bucket_name: t.Optional[str] = None,
    ) -> None:
        self._client: t.Optional[S3ServiceResource] = None
        self._bucket_name: t.Optional[str] = bucket_name
        if access_key and secret_key:
            self.init_s3(access_key, secret_key, region_name)

    def init_s3(
        self,
        access_key: str,
        secret_key: str,
        region_name: str = "us-east-1",
        bucket_name: t.Optional[str] = None,
    ) -> None:
        """Initializes the S3 client with the given AWS credentials and region.

        Args:
            access_key (:obj:`str`): The AWS Access Key.
            secret_key (:obj:`str`): The AWS Secret Key.
            region_name (:obj:`str`): The AWS Region. Defaults to "us-east-1".
            bucket_name (:obj:`str`): The S3 Bucket name.
        """
        self._client = boto3.resource(
            "s3",
            region_name=region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        if bucket_name:
            self._bucket_name = bucket_name

    @property
    def client(self) -> S3ServiceResource:
        """Returns the S3 client this wrapper contains.

        Raises:
            :obj:`AttributeError`: If the S3 client hasn't been initialized with
                AWS credentials.

        Returns:
            :obj:`~mypy_boto3_s3.service_resource.S3ServiceResource`: The S3 client
                object.
        """
        if not self._client:
            raise AttributeError("S3 client was not assigned yet!")
        return self._client

    @property
    def bucket_name(self) -> str:
        """Returns the S3 Bucket name this wrapper operates on.

        Raises:
            :obj:`AttributeError`: If the S3 bucket name hasn't been initialized.

        Returns:
            :obj:`str`: The S3 Bucket name.
        """
        if not self._bucket_name:
            raise AttributeError("Bucket name was not assigned yet!")
        return self._bucket_name

    @property
    def bucket(self) -> Bucket:
        """Returns the S3 Bucket this wrapper operates on.

        Returns:
            :obj:`~mypy_boto3_s3.service_resource.Bucket`: The S3 Bucket.
        """
        return self.client.Bucket(self.bucket_name)

    def create_bucket(self) -> None:
        """Creates the S3 Bucket this wrapper operates on if it does not exist."""
        if not self.bucket in self.client.buckets.all():
            self.bucket.create()

    def add_image(self, image_data: bytes) -> str:
        """Adds an image (and its thumbnail) to the S3 bucket.

        Args:
            image_data (:obj:`bytes`): Bytes encoded image.

        Raises:
            :obj:`RuntimeError`: If gifsicle could not make a thumbnail.

        Returns:
            :obj:`str`: Name of the image in the S3 bucket.
        """
        image_name = secrets.token_hex(16)
        self.bucket.put_object(Key=f"{image_name}.gif", Body=image_data)
        try:
            thumb_cmd = subprocess.run(
                ["gifsicle", "-", "#0", "--resize", "140x140"],
                input=image_data,
                capture_output=True,
                check=True,
            )
            thumb_data = thumb_cmd.stdout
            self.bucket.put_object(Key=f"thumbs/{image_name}.gif", Body=thumb_data)
        except subprocess.CalledProcessError as error:
            # TODO: Handle error better by logging rather than crashing
            raise RuntimeError("Could not make thumbnail") from error
        return image_name

    def update_image(self, image_name: str, image_data: bytes) -> bool:
        """Updates an existing image in the S3 bucket, if there is one.

        Args:
            image_name (:obj:`str`): Name of the image in the S3 bucket.
            image_data (:obj:`bytes`): Bytes encoded image.

        Returns:
            True if the image existed and was updated, otherwise False.
        """
        try:
            s3_object = self.bucket.Object(f"{image_name}.gif")
            s3_object.load()
            self.bucket.put_object(Key=f"{image_name}.gif", Body=image_data)
        except ClientError:
            return False
        return True

    def get_image(self, image_name: str) -> t.Optional[bytes]:
        """Gets an image as bytes from the S3 bucket, if it exists.

        Args:
            image_name (:obj:`str`): Name of the image in the S3 bucket.

        Returns:
            :obj:`bytes`: The image bytes if exists, else None.
        """
        try:
            s3_object = self.bucket.Object(f"{image_name}.gif")
            s3_image: GetObjectOutputTypeDef = s3_object.get()
            image_bytes = s3_image["Body"].read()
            return image_bytes
        except ClientError:
            return None

    def delete_image(self, image_name: str) -> DeleteObjectsOutputTypeDef:
        """Deletes an image (and its thumbnail) if it exists from the S3 bucket.

        Args:
            image_name (:obj:`str`): Name of the image in the S3 bucket.

        Returns:
            :obj:`~mypy_boto3_s3.type_defs.DeleteObjectsOutputTypeDef`: Response
                from S3 about the result of the deletion.
        """
        response: DeleteObjectsOutputTypeDef = self.bucket.delete_objects(
            Delete={
                "Objects": [
                    {"Key": f"{image_name}.gif"},
                    {"Key": f"thumbs/{image_name}.gif"},
                ],
                "Quiet": True,
            }
        )
        return response

    def get_image_url(self, image_name: str) -> str:
        """Gets a presigned URL for an image from the S3 bucket.

        Args:
            image_name (:obj:`str`): Name of the image in the S3 bucket.

        Returns:
            :obj:`str`: Presigned URL for the image in the S3 bucket.
        """
        s3client: S3Client = self.client.meta.client  # type: ignore
        image_url = s3client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": f"{image_name}.gif"},
            ExpiresIn=3600,
        )
        return image_url

    def get_thumb_url(self, image_name: str) -> str:
        """Gets a presigned URL for an image thumbnail from the S3 bucket.

        Args:
            image_name (:obj:`str`): Name of the image in the S3 bucket.

        Returns:
            :obj:`str`: Presigned URL for the thumbnail in the S3 bucket.
        """
        return self.get_image_url(f"thumbs/{image_name}")


auth_manager = AuthManager()
cors = CORS()
db = SQLAlchemy()
redis_client = RedisClient()
rq_queue = RQ()
migrate = Migrate()
s3 = S3()
