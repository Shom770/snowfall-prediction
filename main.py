from itertools import chain
from json import load
from operator import itemgetter
from statistics import median, mean


def retrieve_oni_values() -> dict:
    """
    Reads oni.json and serializes the JSON into a dictionary.

    :return: A dictionary with the key being the year and the value being a list of ONI values for time periods.
    """
    with open("oceanic_nino_index/oni.json") as file:
        return {int(key): value for key, value in load(file).items()}


def retrieve_pdo_values() -> dict:
    """
    Reads pdo.json and serializes the JSON into a dictionary.

    :return: A dictionary with the key being the year and the value being a list of PDO values for time periods.
    """
    with open("teleconnections/pdo.json") as file:
        return {int(key): value for key, value in load(file).items()}


def get_analog(
        year: int,
        look_back: int = 0,
        start_year: int = 1964,
        raise_to: int = 1,
        years_to_return: int = 5
) -> list:
    """
    Uses a year and finds the best analogs regarding ONI & PDO, to find the best analogs.

    :param year: Year to find the best analogs for it.
    :param look_back: When comparing ONI values, this parameter defines how many years the program should look back.
    :param start_year: The year to start all comparisons from.
    :param raise_to: How much to raise the differences by, default is 5.
    :param years_to_return: How many years out of the top analogs to return (default is 5).
    """
    oni_analogs = {}
    oni_values = retrieve_oni_values()
    pdo_analogs = {}
    pdo_values = retrieve_pdo_values()

    if look_back == 0:
        current_oni_progression = oni_values[year]
    else:
        start_year += look_back
        current_oni_progression = list(
            chain.from_iterable(
                [oni_values[specific_year] for specific_year in range(year - look_back, year + 1)]
            )
        )
    current_pdo_progression = pdo_values[year]

    for analog_year in range(start_year, year):
        if look_back == 0:
            analog_oni_progression = oni_values[analog_year]
        else:
            analog_oni_progression = list(
                chain.from_iterable(
                    [oni_values[specific_year] for specific_year in range(analog_year - look_back, analog_year + 1)]
                )
            )
        analog_pdo_progression = pdo_values[analog_year]

        analog_oni_progression = analog_oni_progression[:len(current_oni_progression)]
        analog_pdo_progression = analog_pdo_progression[:len(current_pdo_progression)]

        oni_analogs[analog_year] = [
            abs(analog_oni_value - current_oni_value) ** raise_to
            for analog_oni_value, current_oni_value in zip(analog_oni_progression, current_oni_progression)
        ]
        pdo_analogs[analog_year] = [
            abs(analog_pdo_value - current_pdo_value) ** raise_to
            for analog_pdo_value, current_pdo_value in zip(analog_pdo_progression, current_pdo_progression)
        ]

    oni_analogs = dict(sorted(oni_analogs.items(), key=lambda pair: sum(pair[1])))
    pdo_analogs = dict(sorted(pdo_analogs.items(), key=lambda pair: sum(pair[1])))

    analogs = {}

    for analog_year in range(start_year, year):
        oni_place = list(oni_analogs.keys()).index(analog_year) + 1
        pdo_place = list(pdo_analogs.keys()).index(analog_year) + 1

        analogs[analog_year] = (oni_place + pdo_place) / 2

    analogs = dict(sorted(analogs.items(), key=itemgetter(1)))

    return list(analogs.keys())[:years_to_return]


def analog_snowfalls(analog_years: list, airport: str) -> dict:
    """
    Returns a dictionary containing the median snowfall and the snowfall of each analog based on the years passed in for the analogs and the airport.

    :param analog_years: List of years that are analogs with the requested winter.
    :param airport: A string representing which airport to get the analog snowfall for.
    """
    analog_snowfall_data = {"airport": airport, "season_snowfalls": {}}

    with open(f"snowfall_data/snowfall_{airport.lower()}.json") as file:
        snowfall_data = load(file)

    for year in analog_years:
        analog_snowfall_data["season_snowfalls"][f"{year}-{str(year + 1)[2:]}"] = sum(snowfall_data[str(year)])

    analog_snowfall_data["median"] = median(analog_snowfall_data["season_snowfalls"].values())

    return analog_snowfall_data


def format_analog_data(analog_snowfall_data: dict) -> str:
    """
    Formats analog data to be digestible.

    :param analog_snowfall_data: Dictionary containing analog snowfall data.
    :return: String containing formatted analog data.
    """
    formatted_specific_snowfalls = [
        f"\t\n⚫ {winter}: {snowfall_total:.3f}\""
        for winter, snowfall_total in analog_snowfall_data["season_snowfalls"].items()
    ]

    return (
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"Total snowfall for the 2022-2023 year at {analog_snowfall_data['airport'].upper()}"
        f" predicted to be: {analog_snowfall_data['median']:.2f}\""
        f"\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"Top analogs for {analog_snowfall_data['airport'].upper()} are: {''.join(formatted_specific_snowfalls)}"
    )


def check_accuracy(airport: str, start_year: int = 2010) -> None:
    """
    Checks and prints accuracy by airport with this analog predictor.

    :param airport: Airport to check accuracy for.
    :param start_year: Start year of checking years and their accuracy.
    """
    accuracy = {}

    with open(f"snowfall_data/snowfall_{airport.lower()}.json") as file:
        snowfall_data = load(file)

    for year in range(start_year, 2022):
        accuracy[year] = (analog_snowfalls(
            get_analog(year),
            airport=airport
        )["median"] / sum(snowfall_data[str(year)])) * 100

    formatted_accuracy_by_year = [
        f"\t\n⚫ {year}-{year + 1}: {accuracy:.1f}%"
        for year, accuracy in accuracy.items()
    ]

    print(
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"% of snow predicted by this model versus the actual snow that fell at {airport.upper()} from {start_year} to 2022: {mean(accuracy.values()):.1f}%"
        f"\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"% of predicted snowfall versus actual snowfall by year at {airport.upper()} are: {''.join(formatted_accuracy_by_year)}"
    )


if __name__ == '__main__':
    check_accuracy(airport="IAD", start_year=2010)
    # print(
    #     format_analog_data(
    #         analog_snowfalls(
    #             get_analog(2022),
    #             airport="BWI"
    #         )
    #     )
    # )
