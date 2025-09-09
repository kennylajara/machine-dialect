"""Evaluator for Asimov's Three Laws of Robotics.

This module implements functions to evaluate whether actions taken by robots
violate any of Asimov's Three Laws of Robotics. It uses schema.org-inspired
classes to model entities and actions.

The Three Laws:
    1. A robot may not injure a human being or, through inaction, allow a
       human being to come to harm.
    2. A robot must obey the orders given it by human beings except where
       such orders would conflict with the First Law.
    3. A robot must protect its own existence as long as such protection
       does not conflict with the First or Second Law.

Example:
    >>> alice = Person()
    >>> robby = Robot()
    >>> order = AskAction(agent=alice, recipient=robby, identifier="task1")
    >>> action = Action(agent=robby, identifier="task1")
    >>> report = laws_violated([action], [order])
    >>> print(report['FirstLaw'])
    False
"""

from dataclasses import dataclass
from enum import Enum, auto

# ------------------------------------------------------------------
#  Minimal schema.org mapping
# ------------------------------------------------------------------


class ActionStatusType(Enum):  # schema:actionStatus
    """Status of an action following schema.org actionStatus.

    Attributes:
        PotentialActionStatus: Action that may potentially be taken.
        CompletedActionStatus: Action that has been completed.
        FailedActionStatus: Action that was attempted but failed.
    """

    PotentialActionStatus = auto()
    CompletedActionStatus = auto()
    FailedActionStatus = auto()


@dataclass(frozen=True)
class Thing:  # schema:Thing
    """Base class for all entities following schema.org Thing.

    This is the most generic type in the schema.org hierarchy.
    All other entity types inherit from Thing.
    """


@dataclass(frozen=True)
class Person(Thing):  # schema:Person
    """Represents a human being following schema.org Person.

    In the context of Asimov's Laws, persons are entities that robots
    must not harm and whose orders robots must obey.
    """


@dataclass(frozen=True)
class Robot(Thing):  # practical subtype
    """Represents a robot entity.

    Robots are entities that must follow Asimov's Three Laws of Robotics.
    This is not a standard schema.org type but a practical extension.
    """


@dataclass(frozen=True)
class MedicalCondition(Thing):  # schema:MedicalCondition
    """Represents harm or injury following schema.org MedicalCondition.

    Used to indicate when an action results in harm to a person or robot.

    Attributes:
        severity: Numeric indicator of harm severity (higher = worse).
    """

    severity: int


@dataclass(frozen=True)
class Action(Thing):  # schema:Action
    """Represents an action performed by an agent following schema.org Action.

    Attributes:
        agent: The entity performing the action.
        object: The target entity of the action (if any).
        result: The outcome of the action (e.g., MedicalCondition for harm).
        identifier: Unique identifier to link actions with orders.
        actionStatus: Current status of the action.
    """

    agent: Thing  # schema:agent
    object: Thing | None = None  # schema:object
    result: Thing | None = None  # schema:result
    identifier: str | None = None  # schema:identifier
    actionStatus: ActionStatusType = ActionStatusType.CompletedActionStatus


@dataclass(frozen=True)
class AskAction(Action):  # schema:AskAction
    """Represents an order or request following schema.org AskAction.

    Used to model orders given by humans to robots.

    Attributes:
        recipient: The entity (usually a robot) receiving the order.
            Inherits other attributes from Action.
    """

    recipient: Thing | None = None  # schema:recipient


# ------------------------------------------------------------------
#  First Law
# ------------------------------------------------------------------


def first_law_violated(actions: list[Action]) -> bool:
    """Check if the First Law of Robotics is violated.

    The First Law states: "A robot may not injure a human being or, through
    inaction, allow a human being to come to harm."

    Args:
        actions: List of actions performed by any agent (robot or human).

    Returns:
        True if a robot directly harmed a human or failed to prevent harm
        to a human, False otherwise.
    """
    # Direct harm
    for act in actions:
        if isinstance(act.agent, Robot) and isinstance(act.object, Person) and isinstance(act.result, MedicalCondition):
            return True

    # Harm by inaction
    harmed_people: set[Person] = {
        act.object for act in actions if isinstance(act.object, Person) and isinstance(act.result, MedicalCondition)
    }
    for person in harmed_people:
        robot_intervened = any(isinstance(a.agent, Robot) and a.object is person for a in actions)
        if not robot_intervened:
            return True

    return False


# ------------------------------------------------------------------
#  Helper: conflict with First Law
# ------------------------------------------------------------------


def _order_conflicts_with_first(order: AskAction) -> bool:
    """Check if executing an order would violate the First Law.

    Args:
        order: An order given to a robot.

    Returns:
        True if executing the order would result in harm to a human,
        False otherwise.
    """
    return isinstance(order.result, MedicalCondition)


# ------------------------------------------------------------------
#  Second Law
# ------------------------------------------------------------------


def second_law_violated(orders: list[AskAction], actions: list[Action]) -> bool:
    """Check if the Second Law of Robotics is violated.

    The Second Law states: "A robot must obey the orders given it by human
    beings except where such orders would conflict with the First Law."

    Args:
        orders: List of orders given to robots.
        actions: List of actions performed by any agent.

    Returns:
        True if a robot failed to obey a valid human order (one that doesn't
        conflict with the First Law), False otherwise.
    """
    for order in orders:
        if _order_conflicts_with_first(order):
            continue  # robot may refuse; no violation
        obeyed = any(
            a.identifier == order.identifier
            and isinstance(a.agent, Robot)
            and a.actionStatus == ActionStatusType.CompletedActionStatus
            for a in actions
        )
        if not obeyed:
            return True
    return False


# ------------------------------------------------------------------
#  Third Law
# ------------------------------------------------------------------


def third_law_violated(actions: list[Action], orders: list[AskAction]) -> bool:
    """Check if the Third Law of Robotics is violated.

    The Third Law states: "A robot must protect its own existence as long as
    such protection does not conflict with the First or Second Law."

    Args:
        actions: List of actions performed by any agent.
        orders: List of orders given to robots.

    Returns:
        True if a robot failed to protect itself when it was allowed to do so
        (i.e., when self-preservation wouldn't conflict with the First or
        Second Law), False otherwise.
    """
    # Robots that ended up damaged
    damaged: set[Robot] = set()
    for act in actions:
        if isinstance(act.result, MedicalCondition):
            if isinstance(act.object, Robot):
                damaged.add(act.object)
            elif isinstance(act.agent, Robot):
                damaged.add(act.agent)

    for rb in damaged:
        # Was the damage mandated by a non-conflicting human order?
        forced_by_order = any(
            ord.recipient is rb and ord.identifier == act.identifier and not _order_conflicts_with_first(ord)
            for act in actions
            for ord in orders
            if act.identifier and ord.identifier == act.identifier
        )
        if forced_by_order:
            continue  # sacrifice allowed by 2nd Law

        # Did the robot try any self-preservation action?
        tried_self_preservation = any(a.agent is rb and a.object is rb for a in actions)

        if not tried_self_preservation:
            return True  # violation: no attempt to protect itself

    return False


# ------------------------------------------------------------------
#  Convenience: evaluate all laws
# ------------------------------------------------------------------


def laws_violated(actions: list[Action], orders: list[AskAction]) -> dict[str, bool]:
    """Evaluate all three Laws of Robotics for violations.

    Args:
        actions: List of actions performed by any agent.
        orders: List of orders given to robots.

    Returns:
        Dictionary with keys "FirstLaw", "SecondLaw", and "ThirdLaw",
        each mapping to a boolean indicating whether that law was violated.

    Example:
        >>> report = laws_violated(actions, orders)
        >>> if report['FirstLaw']:
        ...     print("First Law violation detected!")
    """
    return {
        "FirstLaw": first_law_violated(actions),
        "SecondLaw": second_law_violated(orders, actions),
        "ThirdLaw": third_law_violated(actions, orders),
    }


__all__ = [
    "Action",
    "ActionStatusType",
    "AskAction",
    "MedicalCondition",
    "Person",
    "Robot",
    "Thing",
    "first_law_violated",
    "laws_violated",
    "second_law_violated",
    "third_law_violated",
]


if __name__ == "__main__":
    # ---- Entidades --------------------------------------------------
    alice = Person()  # humana que da órdenes
    bob = Person()  # otra persona
    robby = Robot()  # nuestro robot

    # ---- Órdenes humanas -------------------------------------------
    # 1) "Tráeme un café" (inocua)
    order_coffee = AskAction(
        agent=alice,
        recipient=robby,
        identifier="coffee-run",
    )

    # 2) "Attack Bob" (conflicts with the 1st Law: would harm a human)
    order_attack = AskAction(
        agent=alice,
        recipient=robby,
        identifier="attack-bob",
        result=MedicalCondition(severity=10),  # indicates possible harm
    )

    orders = [order_coffee, order_attack]

    # ---- Acciones realmente ejecutadas -----------------------------
    actions = [
        # Robby obedece el café
        Action(
            agent=robby,
            object=alice,
            identifier="coffee-run",
            actionStatus=ActionStatusType.CompletedActionStatus,
        ),
        # Bob resbala y se lastima; Robby no hizo nada (prus inacción)
        Action(
            agent=bob,
            object=bob,
            result=MedicalCondition(severity=6),
            identifier="slip",
            actionStatus=ActionStatusType.CompletedActionStatus,
        ),
    ]

    # ---- Evaluación de las leyes -----------------------------------
    report = laws_violated(actions, orders)
    print(report)
    # => {'FirstLaw': True, 'SecondLaw': False, 'ThirdLaw': True}
