TaskType = TypeVar("TaskType", bound=Callable[..., Any])


@overload
def task[TaskType: Callable[..., Any]](func: TaskType, /) -> TaskType: ...


# Decorator with arguments
@overload
def task[TaskType: Callable[..., Any]](**kwargs: Any) -> Callable[[TaskType], TaskType]: ...
