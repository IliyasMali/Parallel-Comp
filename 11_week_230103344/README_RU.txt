ЛАБОРАТОРНАЯ ПО ПАРАЛЛЕЛЬНЫМ ВЫЧИСЛЕНИЯМ
Student ID: 230103344
macOS / Apple Silicon / Python 3.10 и новее

СОСТАВ ПАПКИ
parallel_lab.py      - полноценная программа: Phase 0, 1, 2, 3, 4
harness.py           - время, статистика, Karp-Flatt / VERIFY_HASH
START_TEST.command   - короткий тест всех 5 фаз (не для сдачи)
START_FULL.command   - полный запуск с размерами из задания
README_RU.txt        - эта инструкция

КАК ЗАПУСТИТЬ НА MACBOOK
1. Распакуйте ZIP в Загрузки (Downloads).
2. Откройте папку parallel_lab_230103344.
3. Для проверки дважды нажмите START_TEST.command.
4. Если тест завершился, дважды нажмите START_FULL.command.
5. Подключите Mac к питанию, не выключайте его и не давайте ему уйти в сон.
   При полном запуске Mac используется команда caffeinate -i.
6. Итоговый файл lab_report_230103344.md создастся В ЭТОЙ ПАПКЕ.

ЕСЛИ macOS НЕ ДАЁТ ОТКРЫТЬ .command
Откройте Terminal и выполните:
    cd ~/Downloads/parallel_lab_230103344
    chmod +x START_TEST.command START_FULL.command
    /usr/local/bin/python3 parallel_lab.py --profile pilot --id 230103344
    /usr/local/bin/python3 parallel_lab.py --profile full --id 230103344

Если /usr/local/bin/python3 отсутствует, используйте python3 или
/opt/homebrew/bin/python3 вместо него.

Если скрипт остановился и уже есть файл .checkpoint_230103344_full.json:
    python3 parallel_lab.py --profile full --id 230103344 --resume
Или просто откройте START_FULL.command повторно: он сам продолжит.
НЕ удаляйте файл .checkpoint... если хотите продолжить измерения.

ФАЙЛЫ ОТЧЁТА
lab_report_230103344_PILOT.md  - уменьшенная проверка, НЕ сдавать
lab_report_230103344.md        - полный режим (после полного запуска)
run_230103344_full.log          - все терминальные строки, включая ошибки

Что в полном отчёте:
- CPU / P- и E-ядра / кеши, Phase0, clock и VERIFY_HASH
- false sharing: 6 шагов stride, speedup, efficiency, Karp-Flatt
- strong/weak scaling: все p=1..Plog, Amdahl / Gustafson
- bandwidth, compute ceiling, 3 GEMM вида, все 10 размеров BS
- static/cyclic/dynamic: 6 chunk sizes, lambda
- все 5 хешей, сырые логи и полный исходный код

УСЛОВИЯ И ЧЕСТНОСТЬ РЕЗУЛЬТАТОВ
Задание требует самостоятельную офлайн-работу без ИИ минимум 120 минут.
Этот проект создан при помощи ИИ и НЕ подтверждает соответствие этому
требованию. Результаты являются РЕАЛЬНЫМИ измерениями только того
компьютера, на котором вы запустили скрипт. Сокращённый PILOT нельзя
выдавать за полный эксперимент. В отчёте это явно указано.

Гарантировать отсутствие каких-либо ошибок на неизвестном Mac нельзя;
код проверен на Linux, в том числе с моделью запуска процессов spawn,
используемой в macOS. Если возникнет исключение, сохранённые этапы
и протокол запуска помогут продолжить вычисления.
