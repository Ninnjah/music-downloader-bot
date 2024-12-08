note-album =
    #t{ $task_id }
    Успешно скачал альбом/сборник: <b>{ $artist } - { $title }</b> количество треков - { $track_count }
note-artist =
    #t{ $task_id }
    Успешно скачал треки исполнителя: <b>{ $artist }</b>
note-playlist =
    #t{ $task_id }
    Успешно скачал плейлист: <b>{ $title }</b> количество треков - { $track_count }
note-track =
    #t{ $task_id }
    Успешно скачал трек: <b>{ $artist } - { $title }</b>

note-fail =
    #t{ $task_id }
    Во время скачивания произошла ошибка - <i>{ $info }</i>