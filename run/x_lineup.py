import pandas as pd
from pathlib import Path
import sys
import argparse
from collections import Counter


def read_sensitivity(options=None):

    if options is None or options.get("gw") is None:
        gw = int(input("What GW are you assessing? "))
        situation = (
            input("Is this a wildcard or preseason (GW1) solve? (y/n) ").strip().lower()
        )
    else:
        gw = options["gw"]
        situation = options.get("situation", "n").strip().lower()

    print()

    # Directory and file handling setup
    directory = "../data/results"
    no_plans = 0
    combinations_counter = {
        "Goalkeeper": Counter(),
        "Defenders": Counter(),
        "Midfielders": Counter(),
        "Forwards": Counter(),
    }

    # Loop through each CSV file
    for filename in Path(directory).glob("*.csv"):
        plan = pd.read_csv(filename)

        # Filter by gameweek (week == gw)
        gw_plan = plan[plan["week"] == gw]

        # Group by 'iter' or unique identifier per plan in the file
        for _, sub_plan in gw_plan.groupby("iter"):
            no_plans += 1  # Count only valid plans from the filtered gameweek

            # Filter players in the lineup (lineup == 1) per sub_plan
            lineup = sub_plan[sub_plan["lineup"] == 1]

            # Get unique combinations by position, enforcing constraints
            gk_combination = (
                frozenset(lineup[lineup["pos"] == "GKP"]["name"])
                if len(lineup[lineup["pos"] == "GKP"]) == 1
                else frozenset()
            )
            def_combination = (
                frozenset(lineup[lineup["pos"] == "DEF"]["name"])
                if 3 <= len(lineup[lineup["pos"] == "DEF"]) <= 5
                else frozenset()
            )
            mid_combination = (
                frozenset(lineup[lineup["pos"] == "MID"]["name"])
                if 3 <= len(lineup[lineup["pos"] == "MID"]) <= 5
                else frozenset()
            )
            fwd_combination = (
                frozenset(lineup[lineup["pos"] == "FWD"]["name"])
                if 1 <= len(lineup[lineup["pos"] == "FWD"]) <= 3
                else frozenset()
            )

            # Increment counters for each position's combinations
            if gk_combination:
                combinations_counter["Goalkeeper"][gk_combination] += 1
            if def_combination:
                combinations_counter["Defenders"][def_combination] += 1
            if mid_combination:
                combinations_counter["Midfielders"][mid_combination] += 1
            if fwd_combination:
                combinations_counter["Forwards"][fwd_combination] += 1

    print(f"Number of plans: {no_plans}")
    print()

    # print(f"Locked next gw: {plan["locked_next_gw"].iloc[0]}")
    # print(f"Banned next gw: {plan['banned_next_gw'].iloc[0]}")
    # print()

    # Convert counters to DataFrames with percentages
    def counter_to_df(counter, total_plans):
        df = pd.DataFrame(
            [
                {
                    "Combination": ", ".join(combo),
                    "#_Lineup": count,
                    "Lineup": (count / total_plans) * 100,
                }
                for combo, count in counter.items()
            ]
        )
        return df

    # Create DataFrames for each position
    keepers_df = counter_to_df(combinations_counter["Goalkeeper"], no_plans)
    defs_df = counter_to_df(combinations_counter["Defenders"], no_plans)
    mids_df = counter_to_df(combinations_counter["Midfielders"], no_plans)
    fwds_df = counter_to_df(combinations_counter["Forwards"], no_plans)

    def print_dataframe(df, title):
        print(f"{title}:")

        # Sort the DataFrame by percentage in descending order
        df = df.sort_values(by="Lineup", ascending=False).reset_index(drop=True)

        # Define the max length for each column for proper alignment
        max_name_len = df["Combination"].str.len().max()
        max_lineup_len = 8  # Lineup column to accommodate integer percentage and %
        max_count_len = max(
            8, df["#_Lineup"].astype(str).str.len().max()
        )  # Minimum length of 8

        # Print the headers first with fixed width formatting
        print(
            f"{'Combination':<{max_name_len}} {'Lineup':<{max_lineup_len}} {'#_Lineup':<{max_count_len}}"
        )

        # Normalize values for Lineup percentages
        df["Lineup_normalized"] = df["Lineup"] / df["Lineup"].max()

        df = df[df["#_Lineup"] > 1]

        # Print each row with calculated widths and color intensity based on normalized values
        for _, row in df.iterrows():
            brightness_lineup = int(
                200 * row["Lineup_normalized"]
            )  # Color intensity based on percentage
            color_lineup = f"\033[38;2;0;{brightness_lineup};{255 - brightness_lineup}m"  # Blue to green gradient

            # Print the percentage without decimals along with the percentage symbol
            formatted_lineup = f"{row['Lineup']:.0f}%"  # No decimals

            print(
                f"{row['Combination']:<{max_name_len}} "
                f"{color_lineup}{formatted_lineup:<{max_lineup_len}}\033[0m "
                f"{color_lineup}{row['#_Lineup']:<{max_count_len}}\033[0m"
            )

        print()  # Add an empty line for separation between tables

    # Print sorted DataFrames with color grading
    print_dataframe(keepers_df, "Goalkeepers")
    print_dataframe(defs_df, "Defenders")
    print_dataframe(mids_df, "Midfielders")
    print_dataframe(fwds_df, "Forwards")


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Summarize sensitivity analysis results"
        )
        parser.add_argument("--gw", type=int, help="Numeric value for 'gw'")
        parser.add_argument(
            "--wildcard",
            choices=["Y", "y", "N", "n"],
            help="'Y' if using wildcard, 'N' otherwise",
        )
        args = parser.parse_args()
        gw_value = args.gw
        is_wildcard = args.wildcard
        read_sensitivity({"gw": gw_value, "situation": is_wildcard})
    except:
        read_sensitivity()
