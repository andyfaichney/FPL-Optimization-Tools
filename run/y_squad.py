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

            # Filter players in the squad (squad == 1) per sub_plan
            squad = sub_plan[sub_plan["squad"] == 1]

            # Get unique combinations by position, enforcing constraints
            gk_combination = (
                frozenset(squad[squad["pos"] == "GKP"]["name"])
                if len(squad[squad["pos"] == "GKP"]) == 2
                else frozenset()
            )
            def_combination = (
                frozenset(squad[squad["pos"] == "DEF"]["name"])
                if len(squad[squad["pos"] == "DEF"]) == 5
                else frozenset()
            )
            mid_combination = (
                frozenset(squad[squad["pos"] == "MID"]["name"])
                if len(squad[squad["pos"] == "MID"]) == 5
                else frozenset()
            )
            fwd_combination = (
                frozenset(squad[squad["pos"] == "FWD"]["name"])
                if 1 <= len(squad[squad["pos"] == "FWD"]) == 3
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
                    "#_Squad": count,
                    "Squad": (count / total_plans) * 100,
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
        df = df.sort_values(by="Squad", ascending=False).reset_index(drop=True)

        # Define the max length for each column for proper alignment
        max_name_len = df["Combination"].str.len().max()
        max_squad_len = 8  # Squad column to accommodate integer percentage and %
        max_count_len = max(
            8, df["#_Squad"].astype(str).str.len().max()
        )  # Minimum length of 8

        # Print the headers first with fixed width formatting
        print(
            f"{'Combination':<{max_name_len}} {'Squad':<{max_squad_len}} {'#_Squad':<{max_count_len}}"
        )

        # Normalize values for Squad percentages
        df["Squad_normalized"] = df["Squad"] / df["Squad"].max()

        df = df[df["#_Squad"] > 1]

        # Print each row with calculated widths and color intensity based on normalized values
        for _, row in df.iterrows():
            brightness_squad = int(
                200 * row["Squad_normalized"]
            )  # Color intensity based on percentage
            color_squad = f"\033[38;2;0;{brightness_squad};{255 - brightness_squad}m"  # Blue to green gradient

            # Print the percentage without decimals along with the percentage symbol
            formatted_squad = f"{row['Squad']:.0f}%"  # No decimals

            print(
                f"{row['Combination']:<{max_name_len}} "
                f"{color_squad}{formatted_squad:<{max_squad_len}}\033[0m "
                f"{color_squad}{row['#_Squad']:<{max_count_len}}\033[0m"
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
