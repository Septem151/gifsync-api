"""Representations for the GifSync API."""
from flask_pyjwt import JWT


class AuthToken:
    """Representation of an auth token used for returning from the GifSync API.

    Args:
        auth_token (:obj:`~flask_pyjwt.JWT`): The JWT token to create a
            representation of.
    """

    def __init__(self, auth_token: JWT) -> None:
        self._auth_token = auth_token

    @property
    def username(self) -> str:
        """Username property of an auth token.

        Returns:
            :obj:`str`: "sub" claim of auth token.
        """
        username = self._auth_token.sub
        if not isinstance(username, str):
            raise ValueError("Token's sub claim must be of type 'str'")
        return username

    @property
    def scope(self) -> dict:
        """Scope property of an auth token.

        Raises:
            :obj:`ValueError`: If the token's scope is not a :obj:`dict` or does
                not contain the keys "admin" and "spotify" as booleans.

        Returns:
            :obj:`dict`: "scope" claim of auth token.
        """
        scope = self._auth_token.scope
        if not isinstance(scope, dict):
            raise ValueError("Token's scope claim must be of type 'dict'")
        if "admin" not in scope or "spotify" not in scope:
            raise ValueError("'admin' and 'spotify' must be in token's scope")
        if not isinstance(scope["admin"], bool) or not isinstance(
            scope["spotify"], bool
        ):
            raise ValueError("'admin' and 'spotify' claims in scope must be booleans")
        return scope

    @property
    def token(self) -> str:
        """A signed auth token.

        Raises:
            :obj:`ValueError`: If the token is not signed.

        Returns:
            :obj:`str`: Signed auth token.
        """
        token = self._auth_token.signed
        if not token:
            raise ValueError("Token must be signed")
        return token

    @property
    def expires_in(self) -> int:
        """The max age (in seconds) of an auth token.

        Raises:
            :obj:`ValueError`: If the token is not signed.

        Returns:
            :obj:`int`: Max age of auth token.
        """
        expires_in = self._auth_token.max_age
        if not expires_in:
            raise ValueError("Token must be signed")
        return expires_in

    def to_json(self) -> dict:
        """The json representation of an auth token.

        Returns:
            :obj:`dict`: Auth token represented in JSON format.
        """
        return {
            "username": self.username,
            "scope": self.scope,
            "token": self.token,
            "expires_in": self.expires_in,
        }


class SpotifyAuthToken:
    """Representation of a Spotify token used for returning from the GifSync API.

    Args:
        token (:obj:`str`): The Spotify token.
        expires_in (:obj:`int`): The time (in seconds) the Spotify token expires in.
    """

    def __init__(self, token: str, expires_in: int) -> None:
        self._token = token
        self._expires_in = expires_in

    @property
    def token(self) -> str:
        """The Spotify token.

        Returns:
            :obj:`str`: Spotify API token.
        """
        return self._token

    @property
    def expires_in(self) -> int:
        """The expiry time (in seconds) of the Spotify token.

        Returns:
            :obj:`int`: The expiry time of the Spotify token.
        """
        return self._expires_in


class Task:
    """Representation of a Task for returning from the GifSync API.

    Args:
        task_id (:obj:`str`): The task's id.
        complete (:obj:`bool`): The completion status of the task.
    """

    def __init__(self, task_id: str, complete: bool) -> None:
        self._task_id = task_id
        self._complete = complete

    @property
    def task_id(self) -> str:
        """The task's id.

        Returns:
            :obj:`str`: Task id.
        """
        return self._task_id

    @property
    def complete(self) -> bool:
        """The task's completion status.

        Returns:
            :obj:`bool`: Whether the task is completed or not.
        """
        return self._complete
