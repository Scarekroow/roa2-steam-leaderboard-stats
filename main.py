import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import requests
import xml.etree.ElementTree as et
from datetime import datetime
from matplotlib import rcParams

XML_CACHE = './cache/xml/'
DF_CACHE = './cache/df.pkl'

# Rivals 2, ranked lite ids
GAME_ID = '2217000'
LEADERBOARD_ID = '14800950'


def download_xml():
    """
    Download and save each xml file provided by the steam xml api
    """
    next_url = f'https://steamcommunity.com/stats/{GAME_ID}/leaderboards/{LEADERBOARD_ID}/?xml=1'

    while next_url is not None:
        xml_raw = requests.get(next_url).text
        xml = et.fromstring(xml_raw)

        start = xml.find('entryStart').text.strip()
        end = xml.find('entryEnd').text.strip()

        with open(f'{XML_CACHE}/{start}-{end}.xml', 'w') as file:
            file.write(xml_raw)
            print(f'saved {file.name}')

        next_url = xml.find("nextRequestURL").text.strip() if xml.find("nextRequestURL") is not None else None


def get_leaderboard_xml():
    """
    If leaderboard xml does not exist, download it
    """
    os.makedirs(os.path.dirname(XML_CACHE), exist_ok=True)
    if len(os.listdir(XML_CACHE)) == 0:
        download_xml()


def xml_to_df():
    """
    Return a dataframe of leaderboard entrants from all xml files
    """
    get_leaderboard_xml()

    all_dfs = []
    for file_name in os.listdir(XML_CACHE):
        file_path = os.path.join(XML_CACHE, file_name)
        df = pd.read_xml(file_path, xpath='.//entry')
        all_dfs.append(df)

    return pd.concat(all_dfs, ignore_index=True)


def get_leaderboard_df():
    """
    Find the leaderboard df in cache, or create a new one
    """

    if os.path.exists(DF_CACHE):
        return pd.read_pickle(DF_CACHE)

    df = xml_to_df()
    df.to_pickle(DF_CACHE)
    print(f'saved {DF_CACHE}')
    return df


def rivals2_plot(combined_df: pd.DataFrame):
    """
    Creates a rank histogram for Rivals of Aether II,
    including both percentages and player counts on the bars.
    """
    # Define bins and labels
    bin_edges = [
        0, 400, 500, 600, 700, 800, 900,
        1000, 1100, 1200, 1300, 1400, 1500,
        combined_df['score'].max() + 1
    ]
    bin_labels = [
        'Stone 0-399', 'Stone 400-499',
        'Bronze 500-599', 'Bronze 600-699',
        'Silver 700-799', 'Silver 800-899',
        'Gold 900-999', 'Gold 1000-1099',
        'Plat 1100-1199', 'Plat 1200-1299',
        'Diamond 1300-1399', 'Diamond 1400-1499',
        'Master 1500+'
    ]
    colors = [
        '#5A5A5A', '#7D7D7D',  # Stone
        '#B87333', '#D18E5F',  # Bronze
        '#C0C0C0', '#D9D9D9',  # Silver
        '#FFD700', '#FFE66D',  # Gold
        '#C5B4E3', '#E3D7F8',  # Plat
        '#00BFFF', '#82CAFF',  # Diamond
        '#50C878'  # Master
    ]

    # Categorize the scores into bins
    ranked_bins = pd.cut(combined_df['score'], bins=bin_edges, labels=bin_labels, right=False)

    # Count players in each rank bin
    rank_counts = ranked_bins.value_counts().reindex(bin_labels)
    total_players = rank_counts.sum()

    # Modern Styling
    rcParams.update({
        "font.size": 12,
        "font.family": "DejaVu Sans",
        "axes.edgecolor": "#333333",
        "axes.linewidth": 1.2,
        "axes.facecolor": "#f4f4f4",
        "grid.color": "#dddddd",
        "xtick.color": "#333333",
        "ytick.color": "#333333",
        "text.color": "#333333",
    })

    # Plotting
    fig, ax = plt.subplots(figsize=(19, 10))
    bars = ax.bar(bin_labels, rank_counts, color=colors, edgecolor="black", linewidth=0.6,)

    # Annotate bars with percentages and counts
    for e, (bar, count) in enumerate(zip(bars, rank_counts)):
        height = bar.get_height()
        percentage = (height / total_players) * 100 if total_players else 0
        if height > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, height - 500,
                    f"{percentage:.1f}%\n({int(count)})\n",
                    ha="center", va="bottom", fontsize=10, color="#333333", weight="bold")

    # Customizing Axes and Titles
    ax.set_title('Rivals II Rank Distribution', fontsize=20, weight="bold", color="#333333")
    ax.set_xlabel("Rank Divisions (Score Range)", fontsize=14, labelpad=15)
    ax.set_ylabel("Number of Players", fontsize=14, labelpad=15)
    ax.set_xticks(range(len(bin_labels)))
    ax.set_xticklabels(bin_labels, rotation=45, ha="right", fontsize=10)
    plt.grid(alpha=0.1, linestyle='--', color="#333333")

    # Total Players Footer
    fig.text(0.92, 0.02, f"{datetime.today().strftime('%Y-%m-%d')} - Total Players: {total_players:,}",
             fontsize=10, color="#333333", ha="right", weight="regular")

    plt.text(0.06, 0.02,
             'By Scarekroow\nhttps://github.com/Scarekroow/roa2-steam-leaderboard-stats/tree/main\n'
             '(Modified version of the original by Sixbux\nhttps://github.com/jacobrlewis/steam-leaderboard-stats)',
             fontsize=10, transform=plt.gcf().transFigure)

    # Adjust layout to prevent overlapping
    plt.subplots_adjust(top=0.85)  # Adjust space above the graph
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Dynamically adjust layout within boundaries
    plt.savefig("rank_distribution.png", dpi=300, transparent=False)
    plt.show()


def rivals2_line_plot(combined_df: pd.DataFrame):
    """
    Creates a line graph showing player count vs. score, with player count, percentage,
    and top percentage of players for each division.
    """
    # Updated bin edges and labels
    bin_edges = [
        0, 500, 700, 900,
        1100, 1300, 1500,
        combined_df['score'].max() + 1
    ]
    bin_labels = [
        'Stone', 'Bronze', 'Silver', 'Gold',
        'Platinum', 'Diamond', 'Master'
    ]
    colors = [
        '#5A5A5A', '#B87333', '#C0C0C0',
        '#FFD700', '#C5B4E3', '#00BFFF', '#50C878'
    ]

    # Create a histogram of player counts for each score
    score_counts = combined_df['score'].value_counts().sort_index()

    # Categorize the scores into bins
    ranked_bins = pd.cut(combined_df['score'], bins=bin_edges, labels=bin_labels, right=False)

    # Count players in each rank bin
    rank_counts = ranked_bins.value_counts().reindex(bin_labels)
    total_players = rank_counts.sum()

    # Calculate cumulative top percentages
    cumulative_top_percentage = rank_counts[::-1].cumsum()[::-1] / total_players * 100

    # Define x (score) and y (player count)
    x = score_counts.index
    y = score_counts.values

    # Create the figure
    plt.figure(figsize=(19, 10))

    # Plot the line graph with markers
    plt.plot(x, y, color='black', linewidth=1, label='Player Count')

    # Highlight divisions with shaded areas
    for i in range(len(bin_edges) - 1):
        # Annotate the division with player count, percentage, and top %
        division_label = (
            f"{bin_labels[i]}\n"
            f"{rank_counts[bin_labels[i]]:,} players\n"
            f"({(rank_counts[bin_labels[i]] / total_players) * 100:.1f}%)\n"
            f"Top {cumulative_top_percentage[bin_labels[i]]:.1f}%"
        )
        plt.axvspan(bin_edges[i], bin_edges[i + 1], color=colors[i % len(colors)], alpha=0.4)
        plt.text(
            (bin_edges[i] + bin_edges[i + 1]) / 2, max(y) * 0.9, division_label,
            fontsize=10, ha='center', va='center', weight='bold', color='#333333'
        )

    # Add labels and title
    plt.xlabel('Score', fontsize=14)
    plt.ylabel('Player Count', fontsize=14)
    plt.title('Rivals II Player Count by Ranked Score', fontsize=18, weight='bold')

    # Set x-axis ticks
    plt.xticks(np.arange(0, max(x) + 1, 100), fontsize=10, rotation=45)
    plt.yticks(np.arange(0, max(y) + 1, 50), fontsize=10)

    # Add a legend for divisions
    handles, labels = plt.gca().get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))  # Remove duplicates
    plt.legend(unique_labels.values(), unique_labels.keys(), title="Divisions", fontsize=12)

    # Add gridlines for better readability
    plt.grid(alpha=0.1, linestyle='--', color="#333333")

    # Add total players footer
    plt.text(0.92, 0.02, f"{datetime.today().strftime('%Y-%m-%d')} - Total Players: {total_players:,}",
             fontsize=10, color="#333333", ha="right", transform=plt.gcf().transFigure)

    plt.text(0.06, 0.02, 'By Scarekroow\nhttps://github.com/Scarekroow/roa2-steam-leaderboard-stats/tree/main',
             fontsize=10, transform=plt.gcf().transFigure)

    # Save and show the plot
    plt.tight_layout()
    plt.savefig('rank_distribution_line.png', dpi=300)
    plt.show()


def generate_leaderboard(df: pd.DataFrame):
    """
    Generates a leaderboard with rank, Steam ID (used as name), and score.

    Parameters:
        df: DataFrame containing 'steamid', 'score', and 'rank'.

    Returns:
        pd.DataFrame: Leaderboard with rank, name, and score.
    """
    # Create the leaderboard DataFrame
    leaderboard = df[['rank', 'steamid', 'score']].copy()
    leaderboard.rename(columns={'steamid': 'name'}, inplace=True)

    # Sort the leaderboard by rank
    leaderboard = leaderboard.sort_values(by='rank').reset_index(drop=True)

    leaderboard.to_csv('leaderboard_output.csv', index=False)

    return leaderboard


if __name__ == '__main__':
    df = get_leaderboard_df()
    rivals2_plot(df)
    rivals2_line_plot(df)
    generate_leaderboard(df)
