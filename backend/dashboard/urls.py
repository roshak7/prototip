from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

# URL-паттерны для приложения dashboard
urlpatterns = [
    # Страница входа в систему
    path('login/', views.CustomLoginView.as_view(), name='login'),
    
    # Страница выхода из системы
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Главная страница (дашборд)
    path('', views.dashboard, name='dashboard'),
    
    # Страница отчетов
    path('reports/', views.reports, name='reports'),
    
    # Страница склада и данные для фильтров
    path('inventory/data/', views.inventory_data, name='inventory_data'),
    path('inventory/', views.inventory, name='inventory'),
    
    # Страница настроек (доступна только администраторам)
    path('settings/', views.settings, name='settings'),
    
    # Страница уведомлений
    path('alerts/', views.alerts, name='alerts'),
    
    # Личный кабинет пользователя
    path('profile/', views.profile, name='profile'),
]
