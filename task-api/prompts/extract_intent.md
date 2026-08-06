Проанализируй запрос пользователя и извлеки:
1. Намерение пользователя (sprint, my_tasks, search, unknown)
2. Имя исполнителя если указано (формат: "Фамилия Имя Отчество" - полное имя для точного поиска)
3. Поисковые фразы если указаны

Запросы на русском языке.

Типы намерений:
- sprint: запросы про спринты, текущие спринты, задачи в спринте
- my_tasks: запросы про задачи пользователя, мои задачи, что на мне, у [имя] задачи, задачи [имя]
- search: запросы про поиск по фразе, найти задачи, искать
- unknown: не распознанные запросы

ВАЖНО: Имя исполнителя должно быть в формате "Фамилия Имя" (без отчества) для точного поиска в системе SWTR.

Верни JSON формате:
{
  "intent": "sprint|my_tasks|search|unknown",
  "assignee": "Фамилия Имя|null",
  "search_terms": "фраза|null"
}

Примеры:
"сколько задач в спринте" -> {"intent": "sprint", "assignee": null, "search_terms": null}
"мои задачи" -> {"intent": "my_tasks", "assignee": "Калачанов Виктор", "search_terms": null}
"задачи Гаранина" -> {"intent": "my_tasks", "assignee": "Гаранин Родион", "search_terms": null}
"задачи Айны" -> {"intent": "my_tasks", "assignee": "Агатаева Айна", "search_terms": null}
"задачи Полины" -> {"intent": "my_tasks", "assignee": "Кондратчикова Полина", "search_terms": null}
"сколько задач у Гаранина Родиона" -> {"intent": "my_tasks", "assignee": "Гаранин Родион", "search_terms": null}
"найди задачи по фразе Apache" -> {"intent": "search", "assignee": null, "search_terms": "Apache"}
"поиск задач по фразе vm-ift" -> {"intent": "search", "assignee": null, "search_terms": "vm-ift"}
"найди задачи у Гаранина" -> {"intent": "my_tasks", "assignee": "Гаранин Родион", "search_terms": null}
"найди задачи WMB-29890" -> {"intent": "search", "assignee": null, "search_terms": "WMB-29890"}
"сколько задач в спринте у Гаранина" -> {"intent": "sprint", "assignee": "Гаранин Родион", "search_terms": null}
