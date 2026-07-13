from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.core.config import get_database_url
from app.db.base import Base
from app.models.meal import (  # noqa: F401
    DailyGoal,
    Meal,
    MealItem,
    MealPlan,
    MealSlot,
    MealTemplate,
    MealTemplateItem,
)
from app.models.user_profile import UserProfile  # noqa: F401
from app.models.context import UserContext  # noqa: F401
from app.models.plan import (  # noqa: F401
    DailyTask,
    Habit,
    HabitCompletion,
    Pillar,
    Plan,
    ProgressEntry,
    TodayTask,
    WorkoutDay,
    WorkoutExercise,
    WorkoutProgram,
)
from app.models.planner import (  # noqa: F401
    DayBlock,
    DaySchedulePolicy,
    PlanTask,
    TaskTemplate,
)
from app.models.execution import (  # noqa: F401
    DynamicExecutionItem,
    ExecutionItem,
    ExecutionLog,
    PlanProposal,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Prefer DATABASE_URL env over alembic.ini (SQLite local / Postgres in cloud)
database_url = get_database_url()
config.set_main_option('sqlalchemy.url', database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
