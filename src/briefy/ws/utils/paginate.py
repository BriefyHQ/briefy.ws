"""Pagination to be used with REST Services."""


class Page(list):
    """A list/iterator representing the items on one page of a larger collection.

    An instance of the "Page" class is created from a _collection_ which is any
    list-like object that allows random access to its elements.

    The instance works as an iterator running from the first item to the last item on the given
    page. The Page.pager() method creates a link list allowing the user to go to other pages.

    A "Page" does not only carry the items on a certain page. It gives you additional information
    about the page in these "Page" object attributes:

    item_count
        Number of items in the collection

        **WARNING:** Unless you pass in an item_count, a count will be
        performed on the collection every time a Page instance is created.

    page
        Number of the current page

    items_per_page
        Maximal number of items displayed on a page

    first_page
        Number of the first page - usually 1 :)

    last_page
        Number of the last page

    previous_page
        Number of the previous page. If this is the first page it returns None.

    next_page
        Number of the next page. If this is the first page it returns None.

    page_count
        Number of pages

    items
        Sequence/iterator of items on the current page

    first_item
        Index of first item on the current page - starts with 1

    last_item
        Index of last item on the current page
    """

    def __init__(
            self,
            collection,
            page: int=1,
            items_per_page: int=20,
            item_count: int=None,
            wrapper_class=None,
            **kwargs
    ):
        """Create a "Page" instance.

        Parameters:

        collection
            Sequence representing the collection of items to page through.

        page
            The requested page number - starts with 1. Default: 1.

        items_per_page
            The maximal number of items to be displayed per page.
            Default: 20.

        item_count (optional)
            The total number of items in the collection - if known.
            If this parameter is not given then the paginator will count
            the number of elements in the collection every time a "Page"
            is created. Giving this parameter will speed up things. In a busy
            real-life application you may want to cache the number of items.

        """
        if collection is not None:
            if wrapper_class is None:
                # Default case. The collection is already a list-type object.
                self.collection = collection
            else:
                # Special case. A custom wrapper class is used to access elements of the collection.
                self.collection = wrapper_class(collection)
        else:
            self.collection = []

        self.collection_type = type(collection)

        # Assign kwargs to self
        self.kwargs = kwargs

        # The self.page is the number of the current page.
        # The first page has the number 1!
        try:
            self.page = int(page)  # make it int() if we get it as a string
        except (ValueError, TypeError):
            self.page = 1
        # normally page should be always at least 1 but the original maintainer
        # decided that for empty collection and empty page it can be...0? (based on tests)
        # preserving behavior for BW compat
        if self.page < 1:
            self.page = 1

        self.items_per_page = items_per_page

        # We subclassed "list" so we need to call its init() method
        # and fill the new list with the items to be displayed on the page.
        # We use list() so that the items on the current page are retrieved
        # only once. In an SQL context that could otherwise lead to running the
        # same SQL query every time items would be accessed.
        # We do this here, prior to calling len() on the collection so that a
        # wrapper class can execute a query with the knowledge of what the
        # slice will be (for efficiency) and, in the same query, ask for the
        # total number of items and only execute one query.
        try:
            first = (self.page - 1) * items_per_page
            last = first + items_per_page
            self.items = list(self.collection[first:last])
        except TypeError:
            raise TypeError(
                'Your collection of type {type_} cannot be handled by paginate'.format(
                    type_=type(self.collection_type)
                )
            )

        # Unless the user tells us how many items the collections has
        # we calculate that ourselves.
        if item_count is not None:
            self.item_count = item_count
        else:
            self.item_count = len(self.collection)

        # Compute the number of the first and last available page
        if self.item_count > 0:
            self.first_page = 1
            self.page_count = ((self.item_count - 1) // self.items_per_page) + 1
            self.last_page = self.first_page + self.page_count - 1

            # Make sure that the requested page number is the range of valid pages
            if self.page > self.last_page:
                self.page = self.last_page
            elif self.page < self.first_page:
                self.page = self.first_page

            # Note: the number of items on this page can be less than
            #       items_per_page if the last page is not full
            self.first_item = (self.page - 1) * items_per_page + 1
            self.last_item = min(self.first_item + items_per_page - 1, self.item_count)

            # Links to previous and next page
            if self.page > self.first_page:
                self.previous_page = self.page-1
            else:
                self.previous_page = None

            if self.page < self.last_page:
                self.next_page = self.page+1
            else:
                self.next_page = None

        # No items available
        else:
            self.first_page = None
            self.page_count = 0
            self.last_page = None
            self.first_item = None
            self.last_item = None
            self.previous_page = None
            self.next_page = None
            self.items = []

        # This is a subclass of the 'list' type. Initialise the list now.
        list.__init__(self, self.items)

    def page_info(self) -> dict:
        """Return a dictionary information about this Page."""
        return {
            'page': self.page,
            'page_count': self.page_count,
            'items_per_page': self.items_per_page,
            'previous_page': self.previous_page,
            'next_page': self.next_page,
            'total': self.item_count,
        }

    def __str__(self) -> str:
        """Display general info about this Page."""
        return (
            'Page:\n'
            'Collection type:        {0.collection_type}\n'
            'Current page:           {0.page}\n'
            'First item:             {0.first_item}\n'
            'Last item:              {0.last_item}\n'
            'First page:             {0.first_page}\n'
            'Last page:              {0.last_page}\n'
            'Previous page:          {0.previous_page}\n'
            'Next page:              {0.next_page}\n'
            'Items per page:         {0.items_per_page}\n'
            'Total number of items:  {0.item_count}\n'
            'Number of pages:        {0.page_count}\n'
            ).format(self)

    def __repr__(self) -> str:
        """Representation of the Page."""
        return(
            '<Page number={page} total={page_count}>'.format(
                page=self.page,
                page_count=self.page_count
            )
        )

    def __call__(self) -> dict:
        """Return a dictionary with page data, pagination info."""
        page_info = self.page_info()
        response = {
            'data': self.items,
            'pagination': page_info,
            'total': page_info['total']
        }
        return response


class SQLOrmWrapper:
    """Wrapper class to access elements of an SQLAlchemy ORM query result."""

    def __init__(self, obj):
        """Initialize SQLOrmWrapper.

        :param obj: SQLAlchemy query.
        """
        self.obj = obj

    def __getitem__(self, range: slice):
        """Get item.

        :return: Number of objects.
        """
        if not isinstance(range, slice):
            raise Exception('__getitem__ without slicing not supported')
        return self.obj[range]

    def __len__(self) -> int:
        """Count number of objects for the query.

        :return: Number of objects.
        """
        return self.obj.count()


class SQLPage(Page):
    """A pagination page that deals with SQLAlchemy ORM objects.

    See the documentation on Page for general information on how to work
    with instances of this class.
    """

    def __init__(self, *args, **kwargs):
        """Initialize SQLPage.

        :param args: Arguments for pagination.
        :param kwargs: Keyword arguments for pagination.
        """
        super().__init__(
            *args,
            wrapper_class=SQLOrmWrapper,
            **kwargs
        )


def sql_wrapper_factory(db_session=None):
    """Wrapper for select.

    :param db_session: SQLAlchemy database session.
    :return: SQLSelectWrapper
    """
    class SQLSelectWrapper:
        """Wrapper class to access elements of an SQLAlchemy SELECT query."""

        def __init__(self, obj):
            """Initialize SQLSelectWrapper."""
            self.obj = obj
            self.db_session = db_session

        def __getitem__(self, range: slice):
            """Get item.

            :return: Number of objects.
            """
            if not isinstance(range, slice):
                raise Exception('__getitem__ without slicing not supported')
            # value for offset
            offset_v = range.start
            limit = range.stop - range.start
            select = self.obj.limit(limit).offset(offset_v)
            return self.db_session.execute(select).fetchall()

        def __len__(self) -> int:
            """Count number of objects for the query.

            :return: Number of objects.
            """
            return self.db_session.execute(self.obj.count()).scalar()

    return SQLSelectWrapper


class SQLSelectPage(Page):
    """A pagination page that deals with SQLAlchemy Select objects.

    See the documentation on Page for general information on how to work
    with instances of this class.
    """

    def __init__(self, db_session, *args, **kwargs):
        """sqlalchemy_connection: SQLAlchemy connection object."""
        wrapper = sql_wrapper_factory(db_session)
        super().__init__(
            *args,
            wrapper_class=wrapper,
            **kwargs
        )


def extract_pagination_from_query_params(query_params: dict) -> dict:
    """Extract pagination information from query_params.

    :param query_params: Dictionary containing query_params for a request.
    :return: Dict
    """
    params = {
        'page': 1,
        'items_per_page': 25
    }
    for key, value in params.items():
        new_value = query_params.get(
            '_{key}'.format(key=key), value
        )
        try:
            value = int(new_value)
        except ValueError:
            continue
        if value > 0:
            params[key] = value
    return params
