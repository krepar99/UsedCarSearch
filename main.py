import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# sets page layout to be configured to wide
st.set_page_config(
    page_title="Used Car Search",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Label data file
DATA_FILE = "vehicles.csv"


# helper functions


def filter_by_column_val(df, column, val):
    """ Filters a column of a dataframe by a given value """
    return df[df[column] == val]


def filter_by_column_range(max, df, column, min=0):
    """ Filters a column of a dataframe by a numerical range """
    return df[(df[column] >= min) & (df[column] <= max)].sort_values(
        by=[column], ascending=False
    )


def capitalize_input_choices(choices):
    """ Capitalize each choice in dropdown options """
    capitalized_choices = [item.capitalize() for item in choices]
    return capitalized_choices


# cache loading the data file so it doesn't have to load each time
@st.cache
def prepare_data(filename):
    # read in dataframe from csv file
    df = pd.read_csv(filename)

    # clean data from all rows with NaN for these columns
    cols_to_drop_nan = [
        "price",
        "model",
        "manufacturer",
        "paint_color",
        "transmission",
        "drive",
        "lat",
        "long",
    ]
    for column in cols_to_drop_nan:
        df = df[df[column].notna()]

    # drop duplicate rows
    df.drop_duplicates(inplace=True)

    # change lat and long to appropiate header names for streamlit
    df.rename(columns={"long": "lon"}, inplace=True)
    df["lat"] = pd.to_numeric(df["lat"])
    df["lon"] = pd.to_numeric(df["lon"])

    return df


# load in dataframe from csv
df = prepare_data(DATA_FILE)


# setup streamlit and widget components for filtering

# slider for filtering by price range
price = st.sidebar.slider("Select a range of values", 0, 300_000, (0, 300_000))
price_min, price_max = price[0], price[1]

# get mean of all cars within price range
st.sidebar.write(f"Searching between ${price_min:,} and ${price_max:,}")

# multiselect dropdown for car manufacturers, gets only unique values
manufacturers = st.sidebar.multiselect(
    "Choose Car Manufacturer",
    capitalize_input_choices(sorted(df["manufacturer"].unique())),
)
# multiselect dropdown for paint color, gets only unique values
paint_colors = st.sidebar.multiselect(
    "Choose Paint Color",
    capitalize_input_choices(sorted(df["paint_color"].unique())),
)
# single select for tranmission type, gets only unique values
transmission = st.sidebar.selectbox(
    "Choose Transmission Type",
    capitalize_input_choices(sorted(df["transmission"].unique())),
)
# single select for drive type, gets only unique values
drive_type = st.sidebar.selectbox(
    "Choose Drive Type", capitalize_input_choices(sorted(df["drive"].unique()))
)

# if a price range is chosen, filter dataframe to price range
if price:
    price_min, price_max = price[0], price[1]
    df = filter_by_column_range(
        column="price", min=price_min, max=price_max, df=df
    )

# if manufacturer option is chosen, filter dataframe to include only these manufacturers
if manufacturers:
    # start with empty query string
    query_string = ""
    # get indexes and values of manufacturer dropdown
    for idx, manufacturer in enumerate(manufacturers):
        # if it is the first item in a list build query condition without OR operator
        if not idx:
            query_string += f"manufacturer == '{manufacturer.lower()}'"
        # for every other item in list, add an OR operator after each expression
        # this is to query for multiple manufacturers
        else:
            query_string += " | "
            query_string += f"manufacturer == '{manufacturer.lower()}'"

    # query data frame with query string that was built above
    df = df.query(query_string)

# if paint color option is chosen, filter dataframe to include only these paint colors
# same technique used for building query string for manufacturers
if paint_colors:
    query_string = ""
    for idx, paint_color in enumerate(paint_colors):
        if not idx:
            query_string = f"paint_color == '{paint_color.lower()}'"
        else:
            query_string += " | "
            query_string += f"paint_color == '{paint_color.lower()}'"

    df = df.query(query_string)

# filter dataframe by drive type
if drive_type:
    df = df[df["drive"] == drive_type.lower()]

# filter dataframe by transmission
if transmission:
    df = df[df["transmission"] == transmission.lower()]

# display mean price for all cars in filtered dataframe
mean = st.sidebar.text(
    f"Mean Price for Results: ${round(df['price'].mean(), 2)}"
)

# split page layout into 2 columns
col1, col2 = st.beta_columns(2)

# data to be displayed in Left Column
with col1:
    # Used markdown to achieve Bold Header
    st.markdown("<h1>Used Car Search</h1>", unsafe_allow_html=True)
    # create counter for results, since index from for loop will reference row number
    i = 1
    # get only top 50 results from dataframe
    for index, row in df.head(50).iterrows():
        # Display relevant search result data for each car
        car_manufacturer = row["manufacturer"].capitalize()
        car_year = int(row["year"])
        car_model = row["model"].capitalize()
        car_price = f"{row['price']:,}"
        st.text(f"{i}. {car_manufacturer} {car_model}({car_year}) ${car_price}")

# data to be displayed in Right Column
with col2:
    # show map of car search results at top
    st.map(df)

    # iterate through each chosen manufacturer and get cheapest car by year for each
    for manufacturer in manufacturers:
        # Dict of Lists to contain data for bar chart
        manufacturer_graph_data = {"year": [], "price": []}
        # filter dataframe by manufacturer and save to different variable
        # so it doesn't overwrite filtering on main dataframe
        man_df = df[df["manufacturer"] == manufacturer.lower()]

        # get only unique years for X ticker values
        years = man_df["year"].unique()
        for year in years:
            # filter by each year
            manufacturer_by_year = man_df[man_df["year"] == year]
            # get cheapest car price in that year
            cheapest_price = manufacturer_by_year["price"].min()
            # add data to data structure
            manufacturer_graph_data["year"].append(year)
            manufacturer_graph_data["price"].append(cheapest_price)

        # create dataframe with bar chart data for easy manipulation
        df_for_data = pd.DataFrame(manufacturer_graph_data)

        # create plot
        fig, ax = plt.subplots()
        # get values from columns for bar chart
        y_axis = df_for_data["price"].values
        x_axis = df_for_data["year"].astype(int).values

        # set bar chart settings
        plt.grid(color="black", linestyle="--", linewidth=0.1)
        plt.title(f"{manufacturer.capitalize()} Cheapest Car By Year")
        ax = plt.bar(x_axis, y_axis, color="blue")

        # display barchart
        st.pyplot(fig)
