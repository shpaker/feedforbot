class FeedForBotError(
    Exception,
):
    ...


class ListenerReceiveError(
    FeedForBotError,
):
    ...


class TransportSendError(
    FeedForBotError,
):
    ...
