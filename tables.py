from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    DECIMAL,
    ForeignKey,
    Enum,
    CheckConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


# Define Enum Types
class WeekdayEnum(enum.Enum):
    Monday = "Monday"
    Tuesday = "Tuesday"
    Wednesday = "Wednesday"
    Thursday = "Thursday"
    Friday = "Friday"
    Saturday = "Saturday"
    Sunday = "Sunday"

    def from_int(value):
        return {
            1: WeekdayEnum.Monday,
            2: WeekdayEnum.Tuesday,
            3: WeekdayEnum.Wednesday,
            4: WeekdayEnum.Thursday,
            5: WeekdayEnum.Friday,
            6: WeekdayEnum.Saturday,
            7: WeekdayEnum.Sunday,
        }.get(value, WeekdayEnum.Monday)


class VehicleTypeEnum(enum.Enum):
    Bus = "Bus"
    Tram = "Tram"


class VehicleStatusEnum(enum.Enum):
    Active = "Active"
    Inactive = "Inactive"


class TicketDiscountTypeEnum(enum.Enum):
    Normal = "Normal"
    Discounted = "Discounted"


class TechnicalIssueStatusEnum(enum.Enum):
    Reported = "Reported"
    Resolved = "Resolved"
    InProgress = "InProgress"


class FineStatusEnum(enum.Enum):
    Paid = "Paid"
    Unpaid = "Unpaid"


class StopTypesEnum(enum.Enum):
    Bus = "Bus"
    Tram = "Tram"
    BusTram = "BusTram"


# Define Models
class AppUser(Base):
    __tablename__ = "app_users"

    id_user = Column(Integer, primary_key=True)
    login = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,4}$'",
            name="valid_email",
        ),
    )


class DriversLicense(Base):
    __tablename__ = "drivers_licenses"

    id_license = Column(Integer, primary_key=True, autoincrement=True)
    issued_on = Column(DateTime, nullable=False)
    expires_on = Column(DateTime, nullable=False)

    __table_args__ = (CheckConstraint("expires_on > issued_on", name="valid_dates"),)


class Driver(Base):
    __tablename__ = "drivers"

    id_driver = Column(Integer, primary_key=True)
    fk_license = Column(
        Integer,
        ForeignKey(
            "drivers_licenses.id_license", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
        unique=True,
    )
    fk_user = Column(
        Integer,
        ForeignKey("app_users.id_user", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        unique=True,
    )


class Stop(Base):
    __tablename__ = "stops"

    id_stop = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(Enum(StopTypesEnum), nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    seating_available = Column(Boolean, nullable=False)
    shelter = Column(Boolean, nullable=False)

    __table_args__ = (
        CheckConstraint("longitude BETWEEN -180 AND 180", name="valid_longitude"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="valid_latitude"),
    )


class Path(Base):
    __tablename__ = "paths"

    id_path = Column(Integer, primary_key=True)
    distance = Column(DECIMAL(10, 2), nullable=False)
    number_of_stops = Column(Integer, nullable=False)
    estimated_travel_time = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("distance > 0", name="valid_distance"),
        CheckConstraint("number_of_stops > 2", name="valid_number_of_stops"),
        CheckConstraint(
            "estimated_travel_time > 0", name="valid_estimated_travel_time"
        ),
    )


class Line(Base):
    __tablename__ = "lines"

    id_line = Column(Integer, primary_key=True)
    number = Column(String(10), unique=True, nullable=False)
    fk_main_path = Column(
        Integer,
        ForeignKey("paths.id_path", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=False,
    )
    avg_frequency = Column(Integer, nullable=False)

    __table_args__ = (CheckConstraint("avg_frequency > 0", name="valid_frequency"),)


class PathStop(Base):
    __tablename__ = "path_stops"

    id_path = Column(
        Integer,
        ForeignKey("paths.id_path", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    id_stop = Column(
        Integer,
        ForeignKey("stops.id_stop", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    path_minute = Column(Integer, nullable=False)

    __table_args__ = (CheckConstraint("path_minute > 0", name="valid_path_minute"),)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id_vehicle = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_number = Column(Integer, unique=True, nullable=False)
    last_technical_inspection = Column(DateTime, nullable=False)
    production_date = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)
    type = Column(Enum(VehicleTypeEnum), nullable=False)
    status = Column(Enum(VehicleStatusEnum), nullable=False)
    air_conditioning = Column(Boolean, nullable=False)

    __table_args__ = (CheckConstraint("capacity > 0", name="valid_capacity"),)


class TechnicalIssue(Base):
    __tablename__ = "technical_issues"

    id_technical_issue = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)
    report_date = Column(DateTime, nullable=False)
    resolve_date = Column(DateTime, nullable=True)
    fk_driver = Column(
        Integer,
        ForeignKey("drivers.id_driver", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=False,
    )
    fk_vehicle = Column(
        Integer,
        ForeignKey("vehicles.id_vehicle", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    status = Column(Enum(TechnicalIssueStatusEnum), nullable=False)
    repair_cost = Column(DECIMAL(10, 2), nullable=True)

    __table_args__ = (
        CheckConstraint("repair_cost >= 0", name="valid_repair_cost"),
        CheckConstraint(
            "(resolve_date IS NULL) OR (resolve_date >= report_date)",
            name="valid_dates",
        ),
    )


class Ride(Base):
    __tablename__ = "rides"

    id_ride = Column(Integer, primary_key=True)
    fk_line = Column(
        Integer,
        ForeignKey("lines.id_line", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    fk_path = Column(
        Integer,
        ForeignKey("paths.id_path", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    fk_vehicle = Column(
        Integer,
        ForeignKey("vehicles.id_vehicle", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=False,
    )
    fk_driver = Column(
        Integer,
        ForeignKey("drivers.id_driver", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=False,
    )
    weekday = Column(Enum(WeekdayEnum), nullable=False)
    start_time = Column(DateTime, nullable=False)


class TicketInspector(Base):
    __tablename__ = "ticket_inspectors"

    id_inspector = Column(Integer, primary_key=True)
    fk_user = Column(
        Integer,
        ForeignKey("app_users.id_user", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )


class Inspection(Base):
    __tablename__ = "inspections"

    id_inspection = Column(Integer, primary_key=True)
    fk_ride = Column(
        Integer,
        ForeignKey("rides.id_ride", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    fk_inspector = Column(
        Integer,
        ForeignKey(
            "ticket_inspectors.id_inspector", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    date = Column(DateTime, nullable=False)

    __table_args__ = (CheckConstraint("date <= CURRENT_TIMESTAMP", name="valid_date"),)


class Passenger(Base):
    __tablename__ = "passengers"

    id_passenger = Column(Integer, primary_key=True)
    fk_user = Column(
        Integer,
        ForeignKey("app_users.id_user", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )


class TicketType(Base):
    __tablename__ = "ticket_types"

    id_ticket_type = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(Enum(TicketDiscountTypeEnum), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    validity_duration = Column(Integer, nullable=False)
    is_discounted = Column(Boolean, nullable=False)

    __table_args__ = (
        CheckConstraint("price > 0", name="valid_price"),
        CheckConstraint("validity_duration > 0", name="valid_validity_duration"),
    )


class Purchase(Base):
    __tablename__ = "purchases"

    id_purchase = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("amount > 0", name="valid_amount"),
        CheckConstraint("date <= CURRENT_TIMESTAMP", name="valid_date"),
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id_ticket = Column(Integer, primary_key=True)
    fk_passenger = Column(
        Integer,
        ForeignKey("passengers.id_passenger", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    fk_purchase = Column(
        Integer,
        ForeignKey("purchases.id_purchase", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    fk_ticket_type = Column(
        Integer,
        ForeignKey(
            "ticket_types.id_ticket_type", ondelete="SET NULL", onupdate="CASCADE"
        ),
        nullable=False,
    )


class Fine(Base):
    __tablename__ = "fines"

    id_fine = Column(Integer, primary_key=True)
    fk_passenger = Column(
        Integer,
        ForeignKey("passengers.id_passenger", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    fk_inspector = Column(
        Integer,
        ForeignKey(
            "ticket_inspectors.id_inspector", ondelete="CASCADE", onupdate="CASCADE"
        ),
        nullable=False,
    )
    amount = Column(DECIMAL(10, 2), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    status = Column(Enum(FineStatusEnum), nullable=False)
    deadline = Column(DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint("deadline > issue_date", name="valid_deadline"),
        CheckConstraint("amount > 0", name="valid_amount"),
    )


class Editor(Base):
    __tablename__ = "editors"

    id_editor = Column(Integer, primary_key=True)
    fk_user = Column(
        Integer,
        ForeignKey("app_users.id_user", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
