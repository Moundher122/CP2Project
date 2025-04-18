from django.contrib import admin

# Register your models here.
from . import models
# Register your models here.
admin.site.register(models.Opportunity)
admin.site.register(models.Application)
admin.site.register(models.Team)
@admin.register(models.TeamInvite)
class TeamInviteAdmin(admin.ModelAdmin):
    list_display = ('createdate', 'inviter', 'receiver', 'status')  # Fields to display in the list view
    list_filter = ('status',)  # Optional: Allows filtering by status
    search_fields = ('inviter__username', 'receiver__username')  # Optional: Allows searching by username of inviter/receiver
    ordering = ('-createdate',)  # Optional: Orders by creation date (descending)