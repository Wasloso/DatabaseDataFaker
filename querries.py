from sqlalchemy import func, text
from db_manager import *


def VehiclesWithoutTechnicalInspection(db: DatabaseManager):
    query = (
        db.session.query(
            Vehicle.id_vehicle, Vehicle.type, Vehicle.last_technical_inspection
        )
        .filter(
            Vehicle.last_technical_inspection < func.now() - text("INTERVAL '1 year'")
        )
        .order_by(Vehicle.last_technical_inspection.asc())
    )
    return generateSql(db, query)


def UnresolvedTechnicalIssues(db: DatabaseManager):
    query = (
        db.session.query(
            TechnicalIssue.id_technical_issue,
            TechnicalIssue.report_date,
            TechnicalIssue.status,
            TechnicalIssue.description,
            Vehicle.id_vehicle,
        )
        .join(Vehicle)
        .filter(TechnicalIssue.status != TechnicalIssueStatusEnum.Resolved)
        .order_by(TechnicalIssue.report_date.asc())
    )
    sql = str(
        query.statement.compile(
            dialect=db.engine.dialect, compile_kwargs={"literal_binds": True}
        )
    )
    return generateSql(db, query)


def TicketInspectorFines(db: DatabaseManager):
    fines = func.count(Fine.id_fine).label("Fines")
    query = (
        db.session.query(
            TicketInspector.id_inspector,
            AppUser.name,
            AppUser.surname,
            fines,
        )
        .join(Fine, Fine.fk_inspector == TicketInspector.id_inspector)
        .join(AppUser, AppUser.id_user == TicketInspector.fk_user)
        .group_by(TicketInspector.id_inspector, AppUser.name, AppUser.surname)
        .order_by(fines.desc())
    )
    return generateSql(db, query)


def generateSql(db: DatabaseManager, query):
    return str(
        query.statement.compile(
            dialect=db.engine.dialect, compile_kwargs={"literal_binds": True}
        )
    )


if __name__ == "__main__":

    manager = DatabaseManager(
        "postgresql+psycopg2://postgres:postgres@localhost:5432/DataBases_P"
    )

    print(VehiclesWithoutTechnicalInspection(manager))
    print(UnresolvedTechnicalIssues(manager))
    print(TicketInspectorFines(manager))
