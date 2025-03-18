import db_manager


def main():
    url = f"postgresql+psycopg2://postgres:postgres@localhost:5432/DataBases_P"
    manager = db_manager.DatabaseManager(url)

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

    prompts = [
        ("users", manager.generate_user),
        ("passengers", manager.generate_passenger),
        ("ticket inspectors", manager.generate_ticket_inspector),
        ("drivers", manager.generate_driver),
        ("editors", manager.generate_editor),
        ("stops", manager.generate_stop),
        ("paths", manager.generate_path),
        ("fines", manager.generate_fine),
        ("ticket types", manager.generate_ticket_types),
        ("tickets", manager.generate_ticket),
        ("vehicles", manager.generate_vehicle),
        ("lines", manager.generate_line),
        ("rides", manager.generate_ride),
        ("inspections", manager.generate_inspection),
        ("technical issues", manager.generate_technical_issue),
    ]

    if input("Clear database? (y/n): ") == "y":
        manager.clear_database()

    for prompt, func in prompts:
        try:
            if prompt == "ticket types":
                regenerate = input("Regenerate ticket types? (y/n): ")
                if regenerate == "y":
                    manager.remove_table_content(db_manager.TicketType)
                    func()
                continue
            count = int(input(f"How many {prompt} would you like to generate? "))
            for _ in range(count):
                data = func()
                manager.insert_data(data)
                if prompt == "paths":
                    pathstops = manager.generate_pathstops(data)
                    for pathstop in pathstops:
                        manager.insert_data(pathstop)
        except ValueError:
            print("Invalid input. Skipping.")
        except Exception as e:
            print(f"Error: {e.with_traceback}.)")
            break


if __name__ == "__main__":
    main()
