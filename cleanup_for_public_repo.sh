#!/bin/bash
# Скрипт очистки проекта от чувствительных данных перед публикацией

set -e

echo "=== Очистка проекта от чувствительных данных ==="

# Создаем временную ветку для очистки
git checkout -b clean-public-release

# 1. Замена ФИО сотрудников на общие имена
echo "Замена ФИО сотрудников..."

# Используем sed для замены всех ФИО на стандартные образцы
# Формат: Замена полного имени и инициалов на "Иванов Иван Иванович"

sed -i '' 's/Калачанов Виктор Вячеславович/Иванов Иван Иванович/g' task-api/config/team_members.yaml
sed -i '' 's/Kalachanov\.V\.V/Kalachev.V.V/g' task-api/config/team_members.yaml

sed -i '' 's/Гаранин Родион Владимирович/Петров Петр Петрович/g' task-api/config/team_members.yaml
sed -i '' 's/Garanin\.R\.V/Petrov.P.P/g' task-api/config/team_members.yaml

sed -i '' 's/Агатаева Айна Жумагалиева/Сидорова Анна Сергеевна/g' task-api/config/team_members.yaml
sed -i '' 's/Agataeva\.A\.Z/Sidorova.A.S/g' task-api/config/team_members.yaml

sed -i '' 's/Алексеев Константин Сергеевич/Смирнов Алексей Дмитриевич/g' task-api/config/team_members.yaml
sed -i '' 's/Alekseev\.K\.S/Smirnov.A.D/g' task-api/config/team_members.yaml

sed -i '' 's/Гальцов Александр Алексеевич/Кузьмин Максим Олегович/g' task-api/config/team_members.yaml
sed -i '' 's/Gal_cov_Aleksandr_Alekseevic/Kuzmin.M.O/g' task-api/config/team_members.yaml
sed -i '' 's/Galtsov\.A\.A/Kuzmin.M.O/g' task-api/config/team_members.yaml

sed -i '' 's/Долговской Евгений Николаевич/Попов Денис Алексеевич/g' task-api/config/team_members.yaml
sed -i '' 's/Dolgovskoj_Evgenij_Nikolaevic/Popov.D.A/g' task-api/config/team_members.yaml
sed -i '' 's/Dolgovskoy\.E\.N/Popov.D.A/g' task-api/config/team_members.yaml

sed -i '' 's/Кондратчикова Полина Игоревна/Новикова Елена Владимировна/g' task-api/config/team_members.yaml
sed -i '' 's/Kondratcikova_Polina_Igorevna/Novikova.E.V/g' task-api/config/team_members.yaml
sed -i '' 's/Kondratchikova\.P\.I/Novikova.E.V/g' task-api/config/team_members.yaml

sed -i '' 's/Крюков Владимир Александрович/Федоров Михаил Сергеевич/g' task-api/config/team_members.yaml
sed -i '' 's/Krukov_Vladimir_Aleksandrovic/Fedorov.M.S/g' task-api/config/team_members.yaml
sed -i '' 's/Kryukov\.V\.A/Fedorov.M.S/g' task-api/config/team_members.yaml

sed -i '' 's/Макошина Верея Валерьевна/Васильева Ольга Анатольевна/g' task-api/config/team_members.yaml
sed -i '' 's/Makosina_Verea_Valer_evna/Vasilieva.O.A/g' task-api/config/team_members.yaml
sed -i '' 's/Makoshina\.V\.V/Vasilieva.O.A/g' task-api/config/team_members.yaml

sed -i '' 's/Моисеев Андрей Николаевич/Михайлов Роман Константинович/g' task-api/config/team_members.yaml
sed -i '' 's/Moiseev_Andrej_Nikolaevic/Mihailov.R.K/g' task-api/config/team_members.yaml
sed -i '' 's/Moiseev\.A\.N/Mihailov.R.K/g' task-api/config/team_members.yaml

sed -i '' 's/Семавин Михаил Михайлович/Павлов Игорь Викторович/g' task-api/config/team_members.yaml
sed -i '' 's/Semavin_Mihail_Mihajlovic/Pavlov.I.V/g' task-api/config/team_members.yaml
sed -i '' 's/Semavin\.M\.M/Pavlov.I.V/g' task-api/config/team_members.yaml

sed -i '' 's/Гончаров Александр Олегович/Соколов Артём Андреевич/g' task-api/config/team_members.yaml
sed -i '' 's/Goncarov_Aleksandr_Olegovic/Sokolov.A.A/g' task-api/config/team_members.yaml
sed -i '' 's/Goncharov\.A\.O/Sokolov.A.A/g' task-api/config/team_members.yaml

sed -i '' 's/Александр Решетник/Михаил Лебедев/g' task-api/config/team_members.yaml
sed -i '' 's/Aleksandr_Resetnik/Mikhail_Lebedev/g' task-api/config/team_members.yaml
sed -i '' 's/Reshetnik\.A/Lebedev.M/g' task-api/config/team_members.yaml

sed -i '' 's/Кузнецов Матвей Сергеевич/Тимофеев Арсений Максимович/g' task-api/config/team_members.yaml
sed -i '' 's/Kuznecov_Matvej_Sergeevic/Timofeev.A.M/g' task-api/config/team_members.yaml
sed -i '' 's/Kuznetsov\.M\.Se/Timofeev.A.M/g' task-api/config/team_members.yaml

sed -i '' 's/Безруков Павел Сергеевич/Андреев Николай Сергеевич/g' task-api/config/team_members.yaml
sed -i '' 's/Bezrukov_Pavel_Sergeevic/Andreev.N.S/g' task-api/config/team_members.yaml
sed -i '' 's/Bezrukov\.P\.S/Andreev.N.S/g' task-api/config/team_members.yaml

sed -i '' 's/Шалдунов Александр Витальевич/Морозов Денис Викторович/g' task-api/config/team_members.yaml
sed -i '' 's/Saldunov_Aleksandr_Vital_evic/Morozov.D.V/g' task-api/config/team_members.yaml
sed -i '' 's/Shaldunov\.A\.V/Morozov.D.V/g' task-api/config/team_members.yaml

# 2. Замена email на фейковые
sed -i '' 's/@sbertech\.ru/@example.com/g' task-api/config/team_members.yaml

# 3. Замена email в других файлах
sed -i '' 's/shaldunov\.a\.v/sidorov.a.v/g' task-api/src/s21_team_performance/services/task_service.py
sed -i '' 's/saldunov\.a\.v/sidorov.a.v/g' task-api/src/s21_team_performance/services/task_service.py

# 4. Удаление путей к личным файлам и папкам
sed -i '' 's|/Users/kalachanov\.v\.v|/home/user|g' add_system_mcp.py fix_gigacode_mcp.py rollback_mcp_fix.py
sed -i '' 's|/Users/kalachanov\.v\.v|/home/user|g' task-api/app/services/swtr_sync_service.py
sed -i '' 's|/Users/kalachanov\.v\.v|/home/user|g' task-api/src/s21_agent/config.py
sed -i '' 's|/Users/kalachanov\.v\.v|/home/user|g' task-api/swtr_sync_cli_v2.py

# 5. Замена username в комментариях
sed -i '' 's/kalachanov\.v\.v/user_login/g' task-api/get_task.py
sed -i '' 's/kalachanov/user_login/g' task-api/get_task.py

# 6. Замена имени в комментариях
sed -i '' 's/Проверка для kalachanov/Проверка для пользователя/g' task-api/get_task.py

echo "=== Файлы обновлены ==="

# Показать статус изменений
git add -A
git status

echo ""
echo "=== Проверка изменений ==="
git diff --stat
