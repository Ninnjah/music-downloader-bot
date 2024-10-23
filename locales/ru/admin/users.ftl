# User list
admin-users-list =
    Вступило за сегодня: <code>{ $income_today }</code>
    Вступило за неделю: <code>{ $income_week }</code>
    Вступило всего: <code>{ $income_total }</code>

    Для быстрого поиска отправьте айди пользователя прямо сейчас

    Список пользователей:
admin-button-list-users = 👥 Пользователи
admin-error-users-notfound = Ни одного пользователя не было найдено

admin-show-user =
    Айди пользователя: <a href='tg://user?id={ NUMBER($user_id, useGrouping: 0) }'><b>{ NUMBER($user_id, useGrouping: 0) }</b></a>

    Имя: <b>{ $firstname }</b>
    Никнейм: <b>{ $username ->
        [0] Отсутствует
        *[other] @{$username}
    }</b>

    Добавлен: <code>{ $created_on }</code>
    Последнее обновление: <code>{ $updated_on }</code>
admin-show-ban = { $banned ->
        [0] Есть доступ к боту ✅
        *[1] Забанен ❌
    }