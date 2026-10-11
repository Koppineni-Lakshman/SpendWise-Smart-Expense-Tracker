
import streamlit as st
import pandas as pd
import plotly.express as px

from datetime import date
from pathlib import Path

from database import (
    create_tables,
    add_transaction,
    get_transactions,
    create_budget_table,
    save_budget,
    get_budgets,
    delete_transaction
)

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="SpendWise | Smart Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# LOAD CSS
# ==========================================

css_file = Path(__file__).parent / "assets" / "style.css"

if css_file.exists():
    st.markdown(
        f"<style>{css_file.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True
    )

# ==========================================
# DATABASE
# ==========================================

create_tables()
create_budget_table()

# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.title("💰 SpendWise")
    st.caption("Your Personal Finance Companion")

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "➕ Add Transaction",
            "📊 Analytics",
            "💰 Budget Planner",
            "📜 Transactions"
        ]
    )

    st.divider()
    st.caption("Track Smart. Spend Better. Save More.")

# ==========================================
# LOAD DATA
# ==========================================

columns = [
    "ID", "Date", "Type",
    "Category", "Amount", "Description"
]

df = pd.DataFrame(
    get_transactions(),
    columns=columns
)

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def money(amount):
    return f"₹{amount:,.2f}"


def format_dates(data):
    result = data.copy()

    result["Date"] = (
        result["Date"].dt.strftime("%d-%m-%Y")
    )

    return result


def show_card(label, amount, icon):
    st.markdown(
        f"""
        <div class="finance-card">
            <div class="finance-label">
                {icon} {label}
            </div>
            <div class="finance-value">
                {money(amount)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_chart(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        margin=dict(l=20, r=20, t=50, b=30)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


def monthly_summary(data):
    monthly = data.dropna(subset=["Date"]).copy()

    monthly["Month"] = (
        monthly["Date"].dt.strftime("%Y-%m")
    )

    summary = (
        monthly.groupby(
            ["Month", "Type"],
            as_index=False
        )["Amount"].sum()
    )

    return summary


# ==========================================
# FINANCIAL CALCULATIONS
# ==========================================

income = df.loc[
    df["Type"] == "Income",
    "Amount"
].sum()

expenses = df.loc[
    df["Type"] == "Expense",
    "Amount"
].sum()

balance = income - expenses

savings_rate = (
    (balance / income) * 100
    if income > 0 else 0
)

# ==========================================
# PAGE 1: DASHBOARD
# ==========================================

if page == "🏠 Dashboard":

    st.title("📊 Financial Overview")
    st.caption("Manage your money with confidence.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        show_card("Total Income", income, "💵")

    with col2:
        show_card("Total Expenses", expenses, "💸")

    with col3:
        show_card("Available Balance", balance, "💰")

    with col4:
        st.metric(
            "📈 Savings Rate",
            f"{savings_rate:.1f}%"
        )

    st.divider()

    left, right = st.columns(2)

    expense_df = df[
        df["Type"] == "Expense"
    ].copy()

    # EXPENSE DISTRIBUTION
    with left:

        st.subheader("🥧 Expense Categories")

        if not expense_df.empty:

            category_data = (
                expense_df.groupby(
                    "Category",
                    as_index=False
                )["Amount"].sum()
            )

            fig = px.pie(
                category_data,
                names="Category",
                values="Amount",
                hole=0.55,
                title="Spending Distribution"
            )

            show_chart(fig)

        else:
            st.info("No expenses recorded yet.")

    # MONTHLY CASH FLOW
    with right:

        st.subheader("📊 Monthly Cash Flow")

        if not df.empty:

            monthly_data = monthly_summary(df)

            if not monthly_data.empty:

                fig = px.bar(
                    monthly_data,
                    x="Month",
                    y="Amount",
                    color="Type",
                    barmode="group",
                    title="Income vs Expenses",
                    text_auto=True
                )

                fig.update_xaxes(
                    type="category",
                    title="Month",
                    tickangle=0
                )

                show_chart(fig)

            else:
                st.info("No valid dates available.")

        else:
            st.info("Add transactions to view trends.")

    st.divider()

    # RECENT TRANSACTIONS
    st.subheader("📜 Recent Transactions")

    if not df.empty:

        recent = df.sort_values(
            ["Date", "ID"],
            ascending=False
        ).head(10).copy()

        recent = format_dates(recent)

        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("Your transactions will appear here.")


# ==========================================
# PAGE 2: ADD TRANSACTION
# ==========================================

elif page == "➕ Add Transaction":

    st.title("➕ Add New Transaction")
    st.caption("Keep track of every rupee.")

    with st.form("transaction_form"):

        trans_date = st.date_input(
            "Transaction Date",
            value=date.today()
        )

        trans_type = st.selectbox(
            "Transaction Type",
            ["Expense", "Income"]
        )

        if trans_type == "Income":
            categories = [
                "Salary",
                "Freelance",
                "Business",
                "Gift",
                "Others"
            ]
        else:
            categories = [
                "Food",
                "Travel",
                "Shopping",
                "Education",
                "Bills",
                "Health",
                "Entertainment",
                "Others"
            ]

        category = st.selectbox(
            "Category",
            categories
        )

        amount = st.number_input(
            "Amount (₹)",
            min_value=1.0,
            step=10.0
        )

        description = st.text_input(
            "Description",
            placeholder="Enter transaction details"
        )

        submitted = st.form_submit_button(
            "💾 Save Transaction",
            use_container_width=True
        )

        if submitted:

            add_transaction(
                str(trans_date),
                trans_type,
                category,
                amount,
                description
            )

            st.success(
                "Transaction saved successfully!"
            )

            st.balloons()


# ==========================================
# PAGE 3: ANALYTICS
# ==========================================

elif page == "📊 Analytics":

    st.title("📊 Expense Analytics")
    st.caption("Understand your spending patterns.")

    expense_df = df[
        df["Type"] == "Expense"
    ].copy()

    if not expense_df.empty:

        category_data = (
            expense_df.groupby(
                "Category",
                as_index=False
            )["Amount"].sum()
        )

        # CATEGORY CHART
        fig = px.bar(
            category_data,
            x="Category",
            y="Amount",
            color="Category",
            title="Category-wise Spending",
            text_auto=True
        )

        show_chart(fig)

        # MONTHLY TREND
        expense_df = expense_df.dropna(
            subset=["Date"]
        ).copy()

        expense_df["Month"] = (
            expense_df["Date"].dt.strftime("%Y-%m")
        )

        monthly_data = (
            expense_df.groupby(
                "Month",
                as_index=False
            )["Amount"].sum()
        )

        if not monthly_data.empty:

            fig2 = px.line(
                monthly_data,
                x="Month",
                y="Amount",
                markers=True,
                title="Monthly Expense Trend"
            )

            fig2.update_xaxes(
                type="category",
                title="Month"
            )

            show_chart(fig2)

        # SMART INSIGHTS
        st.divider()
        st.subheader("💡 Smart Financial Insights")

        highest = category_data.loc[
            category_data["Amount"].idxmax()
        ]

        st.info(
            f"🏆 Highest Spending Category: "
            f"{highest['Category']} "
            f"({money(highest['Amount'])})"
        )

        avg_expense = df.loc[
            df["Type"] == "Expense",
            "Amount"
        ].mean()

        col1, col2 = st.columns(2)

        col1.metric(
            "Average Expense",
            money(avg_expense)
        )

        col2.metric(
            "Total Expense Transactions",
            len(df[df["Type"] == "Expense"])
        )

    else:
        st.info("Add expenses to unlock analytics.")


# ==========================================
# PAGE 4: BUDGET PLANNER
# ==========================================

elif page == "💰 Budget Planner":

    st.title("💰 Monthly Budget Planner")
    st.caption("Plan your spending wisely.")

    selected_month = st.date_input(
        "Select Budget Month",
        value=date.today()
    ).strftime("%Y-%m")

    categories = [
        "Food",
        "Travel",
        "Shopping",
        "Education",
        "Bills",
        "Health",
        "Entertainment",
        "Others"
    ]

    st.subheader("🎯 Set Monthly Budget")

    with st.form("budget_form"):

        category = st.selectbox(
            "Expense Category",
            categories
        )

        budget_amount = st.number_input(
            "Monthly Budget (₹)",
            min_value=1.0,
            step=100.0
        )

        submitted = st.form_submit_button(
            "💾 Save Budget",
            use_container_width=True
        )

        if submitted:

            save_budget(
                selected_month,
                category,
                budget_amount
            )

            st.success("Budget saved successfully!")
            st.rerun()

    st.divider()
    st.subheader("📊 Budget Tracking")

    budgets = get_budgets(selected_month)

    monthly_expenses = df[
        (df["Type"] == "Expense") &
        (
            df["Date"].dt.strftime("%Y-%m")
            == selected_month
        )
    ]

    if budgets:

        total_budget = sum(
            budget for _, budget in budgets
        )

        total_spent = 0

        for category, budget in budgets:

            spent = monthly_expenses.loc[
                monthly_expenses["Category"] == category,
                "Amount"
            ].sum()

            total_spent += spent

            percentage = (
                (spent / budget) * 100
            )

            remaining = budget - spent

            st.markdown(f"### 🏷️ {category}")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Budget",
                money(budget)
            )

            col2.metric(
                "Spent",
                money(spent)
            )

            col3.metric(
                "Remaining",
                money(remaining)
            )

            st.progress(
                min(percentage / 100, 1.0)
            )

            if percentage >= 100:
                st.error(
                    f"⚠️ Budget limit reached or exceeded! "
                    f"{percentage:.1f}% used."
                )

            elif percentage >= 80:
                st.warning(
                    f"⚠️ You have used "
                    f"{percentage:.1f}% of your budget."
                )

            else:
                st.success(
                    f"✅ Budget is on track! "
                    f"{percentage:.1f}% used."
                )

            st.divider()

        st.subheader("📌 Overall Budget Summary")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Allocated Budget",
            money(total_budget)
        )

        col2.metric(
            "Spending in Budgeted Categories",
            money(total_spent)
        )

        col3.metric(
            "Remaining Budget",
            money(total_budget - total_spent)
        )

        st.caption(
            "Only categories with saved budgets "
            "are included in this summary."
        )

    else:
        st.info("No budgets set for this month.")


# ==========================================
# PAGE 5: TRANSACTIONS
# ==========================================

elif page == "📜 Transactions":

    st.title("📜 Transaction History")
    st.caption("Manage your financial records.")

    if not df.empty:

        col1, col2 = st.columns(2)

        with col1:
            selected_type = st.selectbox(
                "Filter by Type",
                ["All", "Income", "Expense"]
            )

        with col2:
            selected_category = st.selectbox(
                "Filter by Category",
                ["All"] + sorted(
                    df["Category"].unique().tolist()
                )
            )

        filtered = df.copy()

        if selected_type != "All":
            filtered = filtered[
                filtered["Type"] == selected_type
            ]

        if selected_category != "All":
            filtered = filtered[
                filtered["Category"] == selected_category
            ]

        filtered = filtered.sort_values(
            ["Date", "ID"],
            ascending=False
        )

        # DISPLAY CLEAN DATE
        display_df = format_dates(filtered)

        st.subheader("📋 All Transactions")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # CSV EXPORT
        csv = display_df.to_csv(index=False)

        st.download_button(
            "📥 Download CSV Report",
            data=csv,
            file_name="spendwise_report.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.divider()

        # DELETE TRANSACTION
        st.subheader("🗑️ Delete Transaction")

        if not filtered.empty:

            transaction_id = st.selectbox(
                "Select Transaction ID",
                filtered["ID"].tolist()
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to delete "
                "this transaction."
            )

            if st.button(
                "🗑️ Delete Transaction",
                disabled=not confirm_delete,
                use_container_width=True
            ):

                delete_transaction(
                    int(transaction_id)
                )

                st.success(
                    "Transaction deleted successfully!"
                )

                st.rerun()

        else:
            st.info(
                "No transactions match your filters."
            )

    else:
        st.info("No transactions available yet.")


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "💰 SpendWise | Smart Expense Tracker "
    "— Built with Python & Streamlit"
)
