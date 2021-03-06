from collections import OrderedDict

from django.conf.urls import patterns, url

from sitetree.utils import tree, item
from sitecats.models import Category

from .forms.forms import BookForm, VideoForm, UserForm, DiscussionForm, ArticleForm, CommunityForm, EventForm, \
    ReferenceForm
from .generics.realms import RealmBase
from .generics.models import RealmBaseModel
from .models import User, Discussion, Book, Video, Place, Article, Community, Event, Reference
from .signals import sig_support_changed
from .views import UserDetailsView, CategoryListingView, PlaceListingView, PlaceDetailsView, UserEditView, \
    ReferenceListingView, ReferenceDetailsView
from .zen import *  # Регистрируем блок сайта с дзеном


def bootstrap_realms(urlpatterns):
    """Инициализирует машинерию областей сайта.

    Принимает на вход urlpatterns из urls.py и модифицирует их.

    :param urlpatterns:
    :return:
    """
    urlpatterns += get_realms_urls()
    connect_signals()
    build_sitetree()
    return urlpatterns


REALMS_REGISTRY = OrderedDict()


def connect_signals():
    """Подключает обработчки сигналов проекта.

    :return:
    """
    sig_support_changed.connect(RealmBaseModel.cache_delete_most_voted_objects)


def register_realms(*classes):
    """Регистрирует области (сущности), которые должны быть доступны на сайте.

    :param classes:
    :return:
    """
    for cls in classes:
        REALMS_REGISTRY[cls.get_names()[0]] = cls


def get_realms():
    """Возвращает словарь зарегистрированных областей сайта,
    индексированный именами областей.

    :return:
    """
    return REALMS_REGISTRY


def get_realm(name):
    """Вернёт объет области по её имени, либо None.

    :param str name:
    :return:
    """
    realms = get_realms()
    realm = None

    try:
        realm = realms[name]
    except KeyError:
        pass

    return realm


def get_sitemaps():
    """Возвращает словарь с sitemap-директивами для поисковых систем.

    :return:
    """
    sitemaps = {}
    for realm in get_realms().values():
        if realm.sitemap_enabled:
            sitemaps[realm.name_plural] = realm.get_sitemap()
    return sitemaps


def get_realms_urls():
    """Возвращает url-шаблоны всех зарегистрированных областей сайта.

    :return:
    """
    url_patterns = []
    for realm in get_realms().values():
        url_patterns += realm.get_urls()
    sitemaps = get_sitemaps()
    if sitemaps:
        url_patterns += patterns(
            '', url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}))
    return url_patterns


def build_sitetree():
    """Строит древо сайта, исходя из доступных областей сайта.

    :return:
    """
    # Потакаем поведению Django 1.7 при загрузке приложений.
    from sitetree.sitetreeapp import register_dynamic_trees, compose_dynamic_tree
    register_dynamic_trees(
        compose_dynamic_tree((
            tree('main', 'Основное дерево', (
                item('Про Python', '/', alias='topmenu', url_as_pattern=False,
                     description='Материалы по языку программирования Python. Книги, видео, сообщества '
                                 'и многое другое.',
                     children=(realm.get_sitetree_items() for realm in get_realms().values())),
                item('Вход', 'login', access_guest=True, in_menu=False, in_breadcrumbs=False),
                item('Личное меню', '#', alias='personal', url_as_pattern=False, access_loggedin=True, in_menu=False,
                     in_sitetree=False, children=(
                        item('Профиль', 'users:details request.user.id', access_loggedin=True, in_breadcrumbs=False,
                             in_sitetree=False),
                        item('Настройки', 'users:edit request.user.id', access_loggedin=True, in_breadcrumbs=False,
                             in_sitetree=False),
                        item('Выход', 'logout', access_loggedin=True, in_breadcrumbs=False, in_sitetree=False),
                )),

            )),
            tree('about', 'О проекте', (
                item('Что такое Python', '/promo/', description='Краткие сведения о языке программирования Python.',
                     url_as_pattern=False),
                item('О проекте', '/about/', description='Информация о проекте pythonz.net.', url_as_pattern=False),
                item('Карта сайта', '/sitemap/', description='Список разделов проекта pythonz.net.',
                     url_as_pattern=False),
                item('Поиск по сайту', '/search/', url_as_pattern=False),
            ))
        )),
        reset_cache=True
    )


BASE_KEYWORDS = 'pythonz, pythonz.net, python, питон, programming, прораммирование, разработка,'


class BookRealm(RealmBase):
    """
    Область с книгами.
    """

    txt_promo = ('Времена и люди сменяют друг друга, а книги остаются. '
                 'Взгляните на них &#8211; фолианты, книжицы и книжонки. '
                 'Ходят слухи, что здесь можно отыскать даже гримуары.')
    txt_form_add = 'Добавить книгу'
    txt_form_edit = 'Изменить данные книги'

    view_listing_description = 'Книги по программированию на языке Python. И просто книги по программированию.'
    view_listing_keywords = '%s книга, books, книги по программированию на питоне' % BASE_KEYWORDS

    model = Book
    form = BookForm
    icon = 'book'

    yawidget_code = 173166


class VideoRealm(RealmBase):
    """
    Область с видео.
    """

    txt_promo = ('Видео уникально в плане возможностей по усвоению материала: '
                 'оно заставляет смотреть, слушать, и даже читать. Попробуйте, вам должно понравится.')
    txt_form_add = 'Добавить видео'
    txt_form_edit = 'Изменить данные видео'

    view_listing_description = 'Видео. Лекции, курсы, доклады, связанные с языком программирования Python.'
    view_listing_keywords = '%s видео, videos, видео по программированию на питоне' % BASE_KEYWORDS

    model = Video
    form = VideoForm
    icon = 'film'

    yawidget_code = 173167


class EventRealm(RealmBase):
    """
    Область с событиями.
    """

    txt_promo = ('События разнообразят жизнь: встречи, лекции, беседы, обмен опытом '
                 'позволяют расширить кругозор, установить связи, приятно провести время. Приобщайтесь.')
    txt_form_add = 'Добавить событие'
    txt_form_edit = 'Изменить событие'

    model = Event
    form = EventForm
    icon = 'calendar'
    sitemap_changefreq = 'daily'


# class OpeningRealm(RealmBase):
#
#     model = Opening
#     form = VideoForm
#     icon = 'briefcase'


class ReferenceRealm(RealmBase):
    """
    Область со справочниками.
    """

    allowed_views = ('listing', 'details', 'add', 'edit')
    syndication_enabled = False

    txt_promo = 'Справочные материалы помогают ориентироваться в языке, узнавать о его возможностях.'
    txt_form_add = 'Дополнить справочник'
    txt_form_edit = 'Редактировать статью'

    view_listing_description = 'Справочные материалы по языку программирования Python.'
    view_listing_keywords = '%s справка, reference, справочник по питону' % BASE_KEYWORDS

    view_listing_base_class = ReferenceListingView
    view_details_base_class = ReferenceDetailsView

    model = Reference
    form = ReferenceForm
    icon = 'search'


class ArticleRealm(RealmBase):
    """
    Область со статьями.
    """

    txt_promo = ('Статьи похожи на рассказы. '
                 'Хорошие статьи, как и хорошие рассказы, хочется читать часто, много и даже с наслаждением.')
    txt_form_add = 'Написать статью'
    txt_form_edit = 'Редактировать статью'

    view_listing_description = 'Статьи, связанные с языком программирования Python.'
    view_listing_keywords = '%s статья, заметки, articles, статьи по программированию на питоне' % BASE_KEYWORDS

    model = Article
    form = ArticleForm
    icon = 'file'

    yawidget_code = 173163


class PlaceRealm(RealmBase):
    """
    Область с географическими объектами (местами).
    """
    txt_promo = ('В какую точку земного шара ни ткни, почти наверняка там найдутся интересные люди, '
                 'события, места. Вот вам карта.')

    view_listing_description = 'Места, так или иначе связанные с языком программирования Python.'
    view_listing_keywords = '%s место, местность, город, село, places, места где программируют на питоне' % BASE_KEYWORDS

    model = Place
    form = VideoForm
    icon = 'picture'
    allowed_views = ('listing', 'details')
    sitemap_changefreq = 'monthly'
    view_listing_base_class = PlaceListingView
    view_details_base_class = PlaceDetailsView


class DiscussionRealm(RealmBase):
    """
    Область обсуждений.
    """

    txt_promo = ('Обсуждения позволяют обмениваться опытом и получать ответы на интересующие вопросы и, конечно, '
                 'делиться своим мнением.')
    txt_form_add = 'Создать обсуждение'
    txt_form_edit = 'Редактировать обсуждение'

    view_listing_description = 'Обсуждения тем, связанных с программированием на pythonz.net.'
    view_listing_keywords = '%s обсуждение, discussions, обсуждения питона' % BASE_KEYWORDS

    model = Discussion
    form = DiscussionForm
    icon = 'list'


class UserRealm(RealmBase):
    """
    Область с персоналиями.
    """

    txt_promo = ('Вокруг люди &#8211; это они пишут статьи и книги, организовывают встречи и делятся мнениями, '
                 'это они могут помочь, подсказать, научить. Здесь упомянуты некоторые.')
    txt_form_edit = 'Изменить настройки'

    view_listing_description = 'Люди, связанные с языком программирования Python.'
    view_listing_keywords = '%s персона, человек, пользователь, users, программист на питоне' % BASE_KEYWORDS

    model = User
    form = UserForm
    icon = 'user'
    allowed_views = ('listing', 'details', 'edit')
    syndication_enabled = False
    sitemap_date_field = 'date_joined'
    view_details_base_class = UserDetailsView
    view_edit_base_class = UserEditView

    @classmethod
    def get_sitetree_details_item(cls):
        return item('{{ user.get_display_name }}', 'users:details user.id', in_menu=False, in_sitetree=False)


class CategoryRealm(RealmBase):
    """
    Область с категориями.
    """

    txt_promo = ('Если всё разложить по полочкам, вероятность найти нужное возрастает. '
                 'На наших полочках сплошь нужные вещи.')

    view_listing_description = ('Категории материалов, связанных с языком программирования Python, '
                                'представленных на pythonz.net.')
    view_listing_keywords = '%s категория, метка, categories, материалы по питону' % BASE_KEYWORDS

    model = Category
    icon = 'tag'
    name = 'category'
    name_plural = 'categories'
    allowed_views = ('listing', 'details')
    ready_for_digest = False
    sitemap_enabled = False
    syndication_enabled = False
    show_on_main = False
    view_listing_title = 'Путеводитель'
    view_listing_base_class = CategoryListingView
    view_details_base_class = CategoryListingView

    @classmethod
    def get_sitetree_details_item(cls):
        return item(
            'Категория «{{ category.parent.title }} — {{ category.title }}»', 'categories:details category.id',
            in_menu=False, in_sitetree=False)


class CommunityRealm(RealmBase):
    """
    Область с сообществами.
    """

    txt_promo = ('Чтобы общаться, узнавать новое и развиваться, люди часто объединяются в сообщества по интересам. '
                 'Вступайте в имеющиеся, создавайте свои.')
    txt_form_add = 'Зарегистрировать сообщество'
    txt_form_edit = 'Редактировать сообщество'

    view_listing_description = 'Сообщества людей интересующихся и занимающихся программированием на языке Python.'
    view_listing_keywords = '%s сообщество, люди, community, сообщества питон' % BASE_KEYWORDS

    name = 'community'
    name_plural = 'communities'
    model = Community
    form = CommunityForm
    icon = 'home'
    sitemap_changefreq = 'daily'


register_realms(
    CategoryRealm,
    BookRealm,
    VideoRealm,
    ArticleRealm,
    ReferenceRealm,
    EventRealm,
    UserRealm,
    PlaceRealm,
    DiscussionRealm,
    CommunityRealm
)
