class FeedForBotError(
    Exception,
): ...


class HttpClientError(
    FeedForBotError,
): ...


class HttpTransportError(
    HttpClientError,
): ...


class HttpResponseError(
    HttpClientError,
): ...


class ListenerReceiveError(
    FeedForBotError,
): ...


class TransportSendError(
    FeedForBotError,
): ...
