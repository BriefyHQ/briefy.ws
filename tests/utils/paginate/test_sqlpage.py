"""Test pagination."""
from briefy.ws.utils import paginate
from sqlalchemy import create_engine
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension

import pytest
import sqlalchemy as sa
import transaction


DBSession = orm.scoped_session(orm.sessionmaker(extension=ZopeTransactionExtension()))

Base = declarative_base()


class Item(Base):
    """An Item."""

    __tablename__ = 'items'

    id = sa.Column(sa.Integer, nullable=False, primary_key=True)


@pytest.fixture()
def session(request):
    """Create new engine based on db_settings fixture.
    :param request: pytest request
    :return: Session.
    """
    database_url = 'sqlite://'
    engine = create_engine(database_url, echo=False)
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    def teardown():
        Base.metadata.drop_all(engine)

    request.addfinalizer(teardown)
    return DBSession


@pytest.fixture()
def sample_data(session):
    """Generate sample data.
    :param session: Database session.
    :return: None
    """
    with transaction.manager:
        for idx in range(1, 50):
            item = Item(id=idx)
            session.add(item)


def test_page(sample_data, session):
    """Test paginate.Page __str__."""
    func = paginate.SQLPage
    data = session.query(Item)
    page = func(data)

    assert page.item_count == 49
    assert page.items_per_page == 20
    assert page.page == 1
    assert page.page_count == 3
    assert page.previous_page is None
    assert page.next_page == 2
    assert len(page) == 20
