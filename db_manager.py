from datetime import timedelta
from typing import OrderedDict
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker
from tables import *
from faker import Faker


class DatabaseManager:
    def __init__(
        self,
        db_url,
    ):
        self.engine = create_engine(
            db_url,
        )
        self.session = sessionmaker(bind=self.engine)()
        self.fake = Faker("pl_PL")

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

    def clear_database(self) -> None:
        meta = MetaData()
        meta.reflect(bind=self.engine)
        with self.engine.begin() as conn:
            for table in reversed(meta.sorted_tables):
                conn.execute(table.delete())
        meta.drop_all(bind=self.engine)
        self.create_tables()

    def generate_user(self) -> AppUser:
        used_logins = [login for (login,) in self.session.query(AppUser.login).all()]
        used_emails = [email for (email,) in self.session.query(AppUser.email).all()]
        while (login := self.fake.user_name()) in used_logins:
            pass
        while (email := self.fake.email()) in used_emails:
            pass
        return AppUser(
            login=login,
            password=self.fake.password(),
            email=email,
            phone_number=self.fake.phone_number(),
            name=self.fake.first_name(),
            surname=self.fake.last_name(),
        )

    def generate_vehicle(self, max_number=1000) -> Vehicle:

        production_date = self.fake.date_time_this_decade()
        last_technical_inspection = self.fake.date_time_between(
            start_date=production_date, end_date="now"
        )
        existing_numbers = [
            vn[0] for vn in self.session.query(Vehicle.vehicle_number).all()
        ]
        vehicle_number = self.fake.random_element(
            [i for i in range(1, max_number) if i not in existing_numbers]
        )
        return Vehicle(
            vehicle_number=vehicle_number,
            production_date=production_date,
            last_technical_inspection=last_technical_inspection,
            type=self.fake.random_elements(
                elements=OrderedDict(
                    [(VehicleTypeEnum.Bus, 0.8), (VehicleTypeEnum.Tram, 0.2)]
                ),
                length=1,
                unique=True,
            )[0],
            status=self.fake.random_elements(
                elements=OrderedDict(
                    [(VehicleStatusEnum.Inactive, 0.1), (VehicleStatusEnum.Active, 0.9)]
                ),
                length=1,
                unique=True,
            )[0],
            air_conditioning=self.fake.boolean(chance_of_getting_true=75),
            capacity=self.fake.random_element([30, 50, 70, 80, 90, 100]),
        )

    def generate_drivers_license(self) -> DriversLicense:
        issued_on = self.fake.date_time_this_decade()
        expires_on = issued_on + timedelta(
            days=self.fake.random_int(min=6 * 365, max=180 * 365, step=30)
        )
        return DriversLicense(
            issued_on=issued_on,
            expires_on=expires_on,
        )

    def generate_driver(self) -> Driver:
        used_license_ids = [
            license_id for (license_id,) in self.session.query(Driver.fk_license).all()
        ]

        avalible_licenses = (
            self.session.query(DriversLicense.id_license).filter(
                DriversLicense.id_license.notin_(used_license_ids)
            )
        ).all()
        fk_user_id = self.get_unused_user_id()

        if not avalible_licenses:
            license = self.generate_drivers_license()
            self.insert_data(license)
            return Driver(fk_user=fk_user_id, fk_license=license.id_license)
        return Driver(
            fk_user=fk_user_id,
            fk_license=self.fake.random_element(avalible_licenses).id_license,
        )

    def generate_passenger(self) -> Passenger:
        return Passenger(fk_user=self.get_unused_user_id())

    def generate_ticket_inspector(self) -> TicketInspector:
        return TicketInspector(fk_user=self.get_unused_user_id())

    def generate_editor(self) -> Editor:
        return Editor(fk_user=self.get_unused_user_id())

    def generate_ticket_types(
        self, basePricePerMinute=0.2, basePricePerDay=6.0
    ) -> None:
        from itertools import product

        minuteTickets = [15, 30, 45, 60, 90]
        maxMinutes = max(minuteTickets)
        dayTickets = [1, 2, 3, 7, 30, 90, 180, 365]
        maxDays = max(dayTickets)
        tickets = []
        for minutes, discount in list(product(minuteTickets, TicketDiscountTypeEnum)):
            durationDiscount = 1 - (minutes / maxMinutes) * 0.35
            discountTypeDiscount = 1 - (
                0.5 if discount == TicketDiscountTypeEnum.Discounted else 0
            )
            price = round(
                (
                    basePricePerMinute
                    * minutes
                    * durationDiscount
                    * discountTypeDiscount
                ),
                2,
            )
            name = f"{minutes} minutes ticket - {discount.name}"
            ticket = TicketType(
                name=name,
                type=discount,
                price=price,
                validity_duration=minutes,
                is_discounted=discount == TicketDiscountTypeEnum.Discounted,
            )
            tickets.append(ticket)

        for days, discount in list(product(dayTickets, TicketDiscountTypeEnum)):
            durationDiscount = 1 - (days / maxDays) * 0.3
            discountTypeDiscount = 1 - (
                0.5 if discount == TicketDiscountTypeEnum.Discounted else 0
            )
            price = round(
                (basePricePerDay * days * durationDiscount * discountTypeDiscount), 2
            )
            name = f"{days} days ticket - {discount.name}"
            tickets.append(
                TicketType(
                    name=name,
                    type=discount,
                    price=price,
                    validity_duration=days * 24 * 60,
                    is_discounted=discount == TicketDiscountTypeEnum.Discounted,
                )
            )
        for ticket in tickets:
            self.insert_data(ticket)
        return None

    def generate_fine(self, baseFinePrice=250) -> Fine:
        passangers = [id for (id,) in self.session.query(Passenger.id_passenger).all()]
        ticket_inspectors = [
            id for (id,) in self.session.query(TicketInspector.id_inspector).all()
        ]
        if not passangers or not ticket_inspectors:
            return None
        issue_date = self.fake.date_time_this_decade()
        deadline = issue_date + timedelta(90)

        return Fine(
            fk_passenger=self.fake.random_element(passangers),
            fk_inspector=self.fake.random_element(ticket_inspectors),
            amount=baseFinePrice,
            issue_date=issue_date,
            deadline=deadline,
            status=self.fake.random_elements(
                elements=OrderedDict(
                    [(FineStatusEnum.Paid, 0.95), (FineStatusEnum.Unpaid, 0.05)]
                ),
                length=1,
            )[0],
        )

    def generate_ticket(self) -> Ticket:
        passengers = [id for (id,) in self.session.query(Passenger.id_passenger).all()]
        ticket_types = [ticket for ticket in self.session.query(TicketType).all()]
        if not passengers or not ticket_types:
            return
        ticket_type = self.fake.random_element(ticket_types)
        purchase = self.generate_purchase(ticket_type.price)
        self.insert_data(purchase)
        return Ticket(
            fk_passenger=self.fake.random_element(passengers),
            fk_purchase=purchase.id_purchase,
            fk_ticket_type=ticket_type.id_ticket_type,
        )

    def generate_purchase(self, amount) -> Purchase:
        date = self.fake.date_time_this_decade()
        return Purchase(amount=amount, date=date)

    def generate_inspection(self) -> Inspection:
        date = self.fake.date_time_this_decade()
        inspectors = [
            id for (id,) in self.session.query(TicketInspector.id_inspector).all()
        ]
        rides = [id for (id,) in self.session.query(Ride.id_ride).all()]
        if not inspectors or not rides:
            return None
        return Inspection(
            fk_inspector=self.fake.random_element(inspectors),
            fk_ride=self.fake.random_element(rides),
            date=date,
        )

    def generate_stop(self, longitude=17.038538, latitude=51.107883, type=None) -> Stop:
        used_names = [name for (name,) in self.session.query(Stop.name).all()]
        while (name := self.fake.street_address()) in used_names:
            pass
        type = (
            type
            if type
            else self.fake.random_elements(
                elements=OrderedDict(
                    [
                        (StopTypesEnum.Bus, 0.6),
                        (StopTypesEnum.Tram, 0.2),
                        (StopTypesEnum.BusTram, 0.2),
                    ]
                ),
                length=1,
            )[0]
        )
        seating_available = self.fake.boolean(chance_of_getting_true=80)
        shelter = self.fake.boolean(chance_of_getting_true=75)
        getNextCoords = (
            lambda x: x + self.fake.random_int(min=-250000, max=250000) / 1000000
        )
        while (latitude := getNextCoords(latitude)) < 50.05 or latitude > 52.15:
            pass
        while (longitude := getNextCoords(longitude)) < 16.5 or longitude > 17.5:
            pass
        return Stop(
            name=name,
            type=type,
            seating_available=seating_available,
            shelter=shelter,
            longitude=longitude,
            latitude=latitude,
        )

    def generate_path(self) -> Path:
        distance = self.fake.random_int(min=5, max=50)
        number_of_stops = self.fake.random_int(min=15, max=30)
        estimated_travel_time = int(distance / 35 * 60 + number_of_stops)
        return Path(
            distance=distance,
            number_of_stops=number_of_stops,
            estimated_travel_time=estimated_travel_time,
        )

    def generate_line(self) -> Line:
        paths = [id for (id,) in self.session.query(Path.id_path).all()]
        if not paths:
            return None
        used_lines_numbers = [
            number for (number,) in self.session.query(Line.number).all()
        ]
        numberGen = lambda: (
            str(self.fake.random_int(min=0, max=999))
            + self.fake.random_elements(
                elements=OrderedDict(
                    [("A", 0.2), ("B", 0.02), ("C", 0.02), ("D", 0.02), ("", 0.92)],
                ),
                length=1,
            )[0]
        )
        while (number := numberGen()) in used_lines_numbers:
            pass
        main_path = self.fake.random_element(paths)
        avg_frequency = self.fake.random_int(min=5, max=90)
        return Line(
            number=number,
            fk_main_path=main_path,
            avg_frequency=avg_frequency,
        )

    def generate_pathstops(self, path: Path) -> list[PathStop]:
        stops = self.session.query(Stop).all()
        if len(stops) < path.number_of_stops:
            print("Not enough stops to generate pathstops")
            return None
        stops = self.fake.random_elements(
            elements=stops, length=path.number_of_stops, unique=True
        )
        initial_stop = stops[0]
        stops = [initial_stop] + sorted(
            stops[1:], key=lambda stop: self.calculate_distance(initial_stop, stop)
        )
        return [
            PathStop(
                id_path=path.id_path,
                id_stop=stop.id_stop,
                path_minute=int(
                    path.estimated_travel_time / path.number_of_stops * (i + 1)
                ),
            )
            for (stop, i) in zip(stops, range(len(stops)))
        ]

    def generate_technical_issue(self) -> TechnicalIssue:
        vehicles = [id for (id,) in self.session.query(Vehicle.id_vehicle).all()]
        drivers = [id for (id,) in self.session.query(Driver.id_driver).all()]
        if not vehicles or not drivers:
            return None
        description = self.fake.text()[0:254]
        report_date = self.fake.date_time_this_decade()
        status = self.fake.random_elements(
            elements=OrderedDict(
                [
                    (TechnicalIssueStatusEnum.Reported, 0.2),
                    (TechnicalIssueStatusEnum.InProgress, 0.3),
                    (TechnicalIssueStatusEnum.Resolved, 0.5),
                ]
            ),
            length=1,
        )[0]
        resolve_date = (
            None
            if status != TechnicalIssueStatusEnum.Resolved
            else self.fake.date_time_between(start_date=report_date, end_date="now")
        )
        repair_cost = (
            0
            if status != TechnicalIssueStatusEnum.Resolved
            else self.fake.random_int(min=50, max=5000)
        )
        return TechnicalIssue(
            description=description,
            report_date=report_date,
            status=status,
            resolve_date=resolve_date,
            repair_cost=repair_cost,
            fk_vehicle=self.fake.random_element(vehicles),
            fk_driver=self.fake.random_element(drivers),
        )

    def generate_ride(self) -> Ride:
        lines = [line for line in self.session.query(Line).all()]
        vehicles = [id for (id,) in self.session.query(Vehicle.id_vehicle).all()]
        drivers = [id for (id,) in self.session.query(Driver.id_driver).all()]
        if not lines or not vehicles or not drivers:
            return None
        line = self.fake.random_element(lines)
        vehicle = self.fake.random_element(vehicles)
        driver = self.fake.random_element(drivers)
        start_time = self.fake.date_time_this_decade()
        weekday = WeekdayEnum.from_int(start_time.weekday() + 1)
        return Ride(
            fk_line=line.id_line,
            fk_vehicle=vehicle,
            fk_driver=driver,
            fk_path=line.fk_main_path,
            start_time=start_time,
            weekday=weekday,
        )

    def calculate_distance(self, stop1: Stop, stop2: Stop) -> float:
        return (
            (stop1.latitude - stop2.latitude) ** 2
            + (stop1.longitude - stop2.longitude) ** 2
        ) ** 0.5

    def get_unused_user_id(self) -> int:
        used_ids = [
            user_id
            for (user_id,) in (
                self.session.query(Driver.fk_user)
                .union(
                    self.session.query(Passenger.fk_user).union(
                        self.session.query(TicketInspector.fk_user).union(
                            self.session.query(Editor.fk_user)
                        )
                    )
                )
                .all()
            )
        ]

        avaliable_ids = (
            self.session.query(AppUser.id_user).filter(AppUser.id_user.notin_(used_ids))
        ).all()

        if not avaliable_ids:
            user = self.generate_user()
            print("No avaliable ids, creating new user: ", user.id_user)
            self.insert_data(user)
            return user.id_user
        return self.fake.random_element(avaliable_ids)[0]

    def remove_table_content(self, table):
        self.session.query(table).delete()
        self.session.commit()

    def insert_data(self, data):
        if data:
            self.session.add(data)
            self.session.commit()


if __name__ == "__main__":
    printRow = lambda data: (
        print(
            [
                (key, value)
                for (key, value) in zip(data.__dict__.keys(), data.__dict__.values())
            ]
        )
        if data
        else print("No data generated")
    )
    url = f"postgresql+psycopg2://postgres:postgres@localhost:5432/DataBases_P"
    db_manager = DatabaseManager(url)
    db_manager.remove_table_content(TechnicalIssue)
