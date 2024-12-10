import streamlit as st
from sqlalchemy.sql import text
from catdb import (
    session,
    ensure_user_exists,
    reset_data,
    Group,
    FinancialGoal
)
from datetime import date, timedelta
import pandas as pd

st.set_page_config(page_title="Kush's Financial Goals Tracker", layout="wide")
st.title("Kush's Financial Goals Tracker")

# Sidebar for Reset Button
with st.sidebar:
    if st.button("Reset Data"):
        reset_data()

def welcome_tab():
    st.header("Welcome to Kush's Financial Goals Tracker")
    st.write("""
        Manage your financial goals with ease! 
        This application helps you to:
        - Set new financial goals.
        - Edit or delete existing goals.
        - View upcoming goals within a selected timeframe.

        Let's get started and achieve your financial aspirations!
    """)

# Tab: Set Financial Goals
def set_financial_goal():
    st.header("Set Financial Goals")

    # Inputs for goal details
    goal_name = st.text_input("Goal Name")
    target_amount = st.number_input("Target Amount ($)", min_value=0.0, step=0.01)
    due_date = st.date_input("Due Date")

    # Inputs for category details
    category_name = st.text_input("Category Name")

    if st.button("Add Financial Goal"):
        try:
            # Start a transaction
            session.begin()

            # Check if category exists, if not, create it
            group = session.query(Group).filter_by(name=category_name).first()
            if not group:
                group = Group(user_id=1, name=category_name)
                session.add(group)
                session.commit()

            # Add the financial goal linked to the category
            new_goal = FinancialGoal(
                user_id=1,
                group_id=group.group_id,
                goal_name=goal_name,
                target_amount=target_amount,
                saved_amount=0.0,
                due_date=due_date
            )
            session.add(new_goal)
            session.commit()

            # Commit transaction
            session.commit()
            st.success(f"Added financial goal '{goal_name}' in category '{category_name}' with target ${target_amount} by {due_date}.")
        except Exception as e:
            # Rollback transaction on error
            session.rollback()
            st.error(f"An error occurred: {e}")
        finally:
            session.close()

def manage_goals():
    st.header("Manage Financial Goals")

    try:
        # Fetch all financial goals
        goals = session.query(FinancialGoal).all()
        if goals:
            goal_names = [goal.goal_name for goal in goals]
            selected_goal = st.selectbox("Select Goal", options=goal_names)
            selected_goal_obj = session.query(FinancialGoal).filter_by(goal_name=selected_goal).first()

            if selected_goal_obj:
                # Edit Goal Details
                st.subheader("Edit Goal Details")
                edit_option = st.radio("Select what to edit", ("Name", "Target Amount", "Due Date", "Category"))

                if edit_option == "Name":
                    new_goal_name = st.text_input("Goal Name", value=selected_goal_obj.goal_name)
                    if st.button("Update Name"):
                        selected_goal_obj.goal_name = new_goal_name
                        session.commit()  # Commit transaction
                        st.success(f"Goal name has been updated to '{new_goal_name}'.")

                elif edit_option == "Target Amount":
                    new_target_amount = st.number_input("Target Amount ($)", min_value=0.0,
                                                        value=selected_goal_obj.target_amount)
                    if st.button("Update Target Amount"):
                        selected_goal_obj.target_amount = new_target_amount
                        session.commit()  # Commit transaction
                        st.success(f"Target amount for '{selected_goal}' has been updated to ${new_target_amount}.")

                elif edit_option == "Due Date":
                    new_due_date = st.date_input("Due Date", value=selected_goal_obj.due_date)
                    if st.button("Update Due Date"):
                        selected_goal_obj.due_date = new_due_date
                        session.commit()  # Commit transaction
                        st.success(f"Due date for '{selected_goal}' has been updated to {new_due_date}.")

                elif edit_option == "Category":
                    # Fetch all categories (groups)
                    groups = session.query(Group).all()
                    group_names = [group.name for group in groups]
                    selected_category_name = st.selectbox("Select New Category", options=group_names)
                    selected_group_obj = session.query(Group).filter_by(name=selected_category_name).first()

                    if st.button("Update Category"):
                        selected_goal_obj.group_id = selected_group_obj.group_id
                        session.commit()  # Commit transaction
                        st.success(f"Category for '{selected_goal}' has been updated to '{selected_category_name}'.")

                # Delete Goal
                st.subheader("Delete Goal")
                if st.checkbox("I want to delete this goal"):
                    if st.button("Confirm Delete"):
                        session.delete(selected_goal_obj)
                        session.commit()  # Commit transaction
                        st.success(f"Goal '{selected_goal}' has been deleted.")
                        st.rerun()

        else:
            st.write("No financial goals found. Please add a goal first.")

    except Exception as e:
        session.rollback()  # Rollback transaction on error
        st.error(f"An error occurred: {e}")

    finally:
        session.close()  # Ensure session is closed


def view_future_goals():
    st.header("View Future Goals")

    # Filtering options
    st.subheader("Filter Goals")
    filter_type = st.radio(
        "Choose Filter Type:",
        ["Next 30 Days", "Next 6 Months", "Next Year", "Specific Date", "Date Range", "By Category"]
    )

    # Determine date range based on filter type
    start_date = None
    end_date = None
    selected_category = None

    if filter_type == "Next 30 Days":
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

    elif filter_type == "Next 6 Months":
        start_date = date.today()
        end_date = start_date + timedelta(days=182)  # approx. 6 months

    elif filter_type == "Next Year":
        start_date = date.today()
        end_date = start_date + timedelta(days=365)

    elif filter_type == "Specific Date":
        selected_date = st.date_input("Select a Date", value=date.today())
        start_date = end_date = selected_date

    elif filter_type == "Date Range":
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
        end_date = st.date_input("End Date", value=date.today())

        if start_date > end_date:
            st.error("Start date cannot be after the end date.")
            return

    elif filter_type == "By Category":
        # Fetch all available categories
        try:
            session.begin()
            groups = session.query(Group).all()
            group_names = [group.name for group in groups]
            session.commit()
        except Exception as e:
            session.rollback()
            st.error(f"An error occurred while fetching categories: {e}")
            return
        finally:
            session.close()

        selected_category = st.selectbox("Select Category", options=group_names)

    # Query data with filtering logic
    try:
        session.begin()
        query = text("""
            SELECT g.goal_name, g.target_amount, g.due_date, g.status, grp.name AS category_name
            FROM Goals g
            LEFT JOIN Groups grp ON g.group_id = grp.group_id
            WHERE (:start_date IS NULL OR g.due_date >= :start_date)
              AND (:end_date IS NULL OR g.due_date <= :end_date)
              AND (:selected_category IS NULL OR grp.name = :selected_category)
            ORDER BY g.due_date
        """)
        results = session.execute(query, {
            "start_date": start_date,
            "end_date": end_date,
            "selected_category": selected_category
        }).fetchall()
        session.commit()
    except Exception as e:
        session.rollback()
        st.error(f"An error occurred while fetching goals: {e}")
        return
    finally:
        session.close()

    # Display results
    if results:
        # Convert results to DataFrame
        goals_df = pd.DataFrame(results, columns=["Goal Name", "Target Amount", "Due Date", "Status", "Category Name"])

        # Display filtered data
        st.subheader("Filtered Goals")
        st.dataframe(goals_df.style.format({"Target Amount": "${:,.2f}"}).set_properties(
            **{'font-size': '14px', 'background-color': '#f9f9f9'}
        ), width=1000, height=500)

        # --- Add Summary Statistics ---
        st.markdown("---")
        st.subheader("Summary Statistics")
        total_goals = len(goals_df)
        total_target_amount = goals_df["Target Amount"].sum()
        average_target_amount = goals_df["Target Amount"].mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Goals", total_goals)
        with col2:
            st.metric("Total Target Amount", f"${total_target_amount:,.2f}")
        with col3:
            st.metric("Average Target Amount", f"${average_target_amount:,.2f}")

        # --- Add Graphical Representations ---
        st.markdown("---")
        st.subheader("Graphical Insights")

        # Bar Chart for Target Amounts by Goal
        st.markdown("### Target Amounts by Goal")
        bar_chart_data = goals_df[["Goal Name", "Target Amount"]]
        st.bar_chart(bar_chart_data.set_index("Goal Name"))

    else:
        st.write("No goals found for the selected criteria.")


# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Welcome", "Set Goals", "Manage Goals", "View Future Goals"
])

with tab1:
    welcome_tab()
with tab2:
    set_financial_goal()
with tab3:
    manage_goals()
with tab4:
    view_future_goals()

# Ensure User Exists
ensure_user_exists()
session.close()
