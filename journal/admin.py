from django.contrib import admin

from .models import Journalist, Category, News, Image, Tag, Newsletter, Video, Comment, Answer, \
    SignalComment, SignalAnswer, CommentFilter, ImageNews


admin.site.register(Journalist)
admin.site.register(Category)
admin.site.register(News)
admin.site.register(Image)
admin.site.register(Tag)
admin.site.register(Newsletter)
admin.site.register(Video)
admin.site.register(Comment)
admin.site.register(Answer)
admin.site.register(SignalComment)
admin.site.register(SignalAnswer)
admin.site.register(CommentFilter)
admin.site.register(ImageNews)
