from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
import streamlit as st

# Creating the database
engine = create_engine('sqlite:///cat_kush_budget_tracker.db', isolation_level="SERIALIZABLE")
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# User Table
class User(Base):
    __tablename__ = 'Users'
    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    goals = relationship("FinancialGoal", back_populates="user")
    groups = relationship("Group", back_populates="user")


# Group Table (without description)
class Group(Base):
    __tablename__ = 'Groups'
    group_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    name = Column(String, nullable=False)
    user = relationship("User", back_populates="groups")
    goals = relationship("FinancialGoal", back_populates="group")


# Financial Goal Table
class FinancialGoal(Base):
    __tablename__ = 'Goals'
    goal_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    group_id = Column(Integer, ForeignKey('Groups.group_id'))
    goal_name = Column(String)
    target_amount = Column(Float)
    saved_amount = Column(Float, default=0.0)
    due_date = Column(Date)
    status = Column(String, default="In Progress")
    user = relationship("User", back_populates="goals")
    group = relationship("Group", back_populates="goals")


# Create tables
Base.metadata.create_all(engine)

# Add indexes for optimization
session.execute(text("CREATE INDEX IF NOT EXISTS idx_due_date ON Goals(due_date);"))
session.execute(text("CREATE INDEX IF NOT EXISTS idx_goal_name ON Goals(goal_name);"))
session.execute(text("CREATE INDEX IF NOT EXISTS idx_group_name ON Groups(name);"))

# Ensure a default user exists
def ensure_user_exists():
    user = session.query(User).filter_by(user_id=1).first()
    if not user:
        new_user = User(user_id=1, name="John Doe", email="JohnDoe@example.com")
        session.add(new_user)
        session.commit()


# Reset all data
def reset_data():
    tables = ['Goals', 'Groups', 'Users']
    for table in tables:
        session.execute(text(f"DELETE FROM {table}"))
        session.commit()
    st.success("All data has been reset!")
