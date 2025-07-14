"""
Скрипт для запуска симулятора жизни
Поддерживает как веб-интерфейс, так и консольный режим
"""

import argparse
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Импортируем необходимые модули
import sys
# Добавляем родительскую папку (на уровень выше) в путь поиска
sys.path.append(str(Path(__file__).parent.parent))

from models import Person, HistoryEvent
from profiles_loader import try_parse_json
from uuid import uuid4
from transaction_simulator.life_simulator import LifeTransactionSimulator
from transaction_simulator.transaction_models import SimulationConfig
from transaction_simulator.report_generator import ReportGenerator
from flask import Flask, render_template_string, request, jsonify, Response, stream_with_context
import threading
import queue

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # Отключаем кеш для разработки

FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Life Simulator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        form {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .form-row {
            margin: 10px 0;
        }
        label {
            display: inline-block;
            width: 140px;
            margin-right: 10px;
        }
        input, select {
            margin: 5px 0;
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
        }
        input[type="submit"] {
            background: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            margin-top: 10px;
            width: auto;
        }
        input[type="submit"]:hover {
            background: #0056b3;
        }
        #output {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            max-height: 600px;
            overflow-y: auto;
        }
        .loading {
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>🌟 Life Transaction Simulator</h1>
    <form id="simForm">
        <div class="form-row">
            <label>Имя:</label>
            <input type="text" name="name" value="Александр Петров" required>
        </div>
        <div class="form-row">
            <label>Возраст:</label>
            <input type="number" name="age" value="28" min="14" max="80" required>
        </div>
        <div class="form-row">
            <label>Пол:</label>
            <select name="gender">
                <option value="мужчина">мужчина</option>
                <option value="женщина">женщина</option>
            </select>
        </div>
        <div class="form-row">
            <label>Профессия:</label>
            <input type="text" name="profession" value="менеджер" required>
        </div>
        <div class="form-row">
            <label>Доход:</label>
            <select name="income">
                <option value="низкий">низкий</option>
                <option value="средний" selected>средний</option>
                <option value="высокий">высокий</option>
            </select>
        </div>
        <div class="form-row">
            <label>Образование:</label>
            <select name="education">
                <option value="">—</option>
                <option value="среднее">среднее</option>
                <option value="среднее специальное">среднее специальное</option>
                <option value="неполное высшее">неполное высшее</option>
                <option value="высшее">высшее</option>
            </select>
        </div>
        <div class="form-row">
            <label>Регион:</label>
            <input type="text" name="region" value="Москва" required>
        </div>
        <div class="form-row">
            <label>Тип города:</label>
            <select name="city_type">
                <option value="село">село</option>
                <option value="малый город">малый город</option>
                <option value="средний город">средний город</option>
                <option value="крупный город">крупный город</option>
                <option value="мегаполис" selected>мегаполис</option>
            </select>
        </div>
        <div class="form-row">
            <label>Семейное положение:</label>
            <select name="family_status">
                <option value="не женат" selected>не женат</option>
                <option value="женат/замужем">женат/замужем</option>
                <option value="разведен">разведен</option>
                <option value="вдовец/вдова">вдовец/вдова</option>
            </select>
        </div>
        <div class="form-row">
            <label>Детей:</label>
            <input type="number" name="children" value="0" min="0" max="10">
        </div>
        <div class="form-row">
            <label>Религия:</label>
            <select name="religion">
                <option value="">—</option>
                <option value="православие">православие</option>
                <option value="ислам">ислам</option>
                <option value="атеизм">атеизм</option>
                <option value="другое">другое</option>
            </select>
        </div>
        <div class="form-row">
            <label>Идеология:</label>
            <select name="ideology">
                <option value="">—</option>
                <option value="левые">левые</option>
                <option value="правые">правые</option>
                <option value="либералы">либералы</option>
                <option value="консерваторы">консерваторы</option>
            </select>
        </div>
        <div class="form-row">
            <label>Цифровая грамотность:</label>
            <select name="digital_literacy">
                <option value="">—</option>
                <option value="низкая">низкая</option>
                <option value="средняя">средняя</option>
                <option value="высокая">высокая</option>
            </select>
        </div>
        <div class="form-row">
            <label>Контекст:</label>
            <input type="text" name="context">
        </div>
        <div class="form-row">
            <label>Когнитивная рамка:</label>
            <textarea name="cognitive_frame" placeholder="можно оставить пустым"></textarea>
        </div>
        <div class="form-row">
            <label>Риторическая манера:</label>
            <textarea name="rhetorical_manner" placeholder="можно оставить пустым"></textarea>
        </div>
        <div class="form-row">
            <label>Триггерные точки:</label>
            <input type="text" name="trigger_points" placeholder="можно оставить пустым, список через запятую">
        </div>
        <div class="form-row">
            <label>Когнитивные искажения:</label>
            <textarea name="interpretation_biases" placeholder="можно оставить пустым"></textarea>
        </div>
        <div class="form-row">
            <label>Взгляд на себя:</label>
            <textarea name="meta_self_view" placeholder="можно оставить пустым"></textarea>
        </div>
        <div class="form-row">
            <label>Речевой профиль:</label>
            <textarea name="speech_profile" placeholder="можно оставить пустым"></textarea>
        </div>
        <div class="form-row">
            <label>Дополнительные факты (JSON):</label>
            <textarea name="full_history" placeholder="можно оставить пустым"></textarea>
        </div>
        <div class="form-row">
            <label>Дней симуляции:</label>
            <input type="number" name="days" value="3" min="1" max="30" required>
        </div>
        <div class="form-row">
            <label>Дата начала:</label>
            <input type="date" name="start_date">
        </div>
        <div class="form-row">
            <input type="submit" value="🚀 Запустить симуляцию">
        </div>
    </form>
    <pre id="output"></pre>

<script>
(function() {
    'use strict';
    
    // Ждём загрузки DOM
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM loaded, initializing form handler');
        
        const form = document.getElementById('simForm');
        const output = document.getElementById('output');
        
        if (!form) {
            console.error('Form not found!');
            return;
        }
        
        form.addEventListener('submit', function(e) {
            console.log('Form submitted');
            e.preventDefault();
            e.stopPropagation();
            
            // Собираем данные формы
            const formData = new FormData(form);
            const params = new URLSearchParams(formData);
            
            // Очищаем вывод
            output.textContent = '⏳ Запускаем симуляцию...\\n';
            output.className = 'loading';
            
            // Создаём EventSource
            const url = '/simulate_stream?' + params.toString();
            console.log('Connecting to:', url);
            
            const eventSource = new EventSource(url);
            
            eventSource.onopen = function() {
                console.log('EventSource connected');
                output.className = '';
            };
            
            eventSource.onmessage = function(event) {
                console.log('Received event:', event.data.substring(0, 100) + '...');
                
                try {
                    const msg = JSON.parse(event.data);
                    
                    if (msg.event === 'environment') {
                        output.textContent += '\\n🔹 Социальное окружение:\\n';
                        
                        if (msg.data.close_circle && msg.data.close_circle.length > 0) {
                            output.textContent += '\\n📍 Близкий круг:\\n';
                            msg.data.close_circle.forEach(function(p) {
                                output.textContent += '  • ' + p.name + ' (' + p.relation + ', ' + (p.age || '?') + ' лет)';
                                if (p.description) {
                                    output.textContent += ' - ' + p.description;
                                }
                                output.textContent += '\\n';
                            });
                        }
                        
                        if (msg.data.extended_circle && msg.data.extended_circle.length > 0) {
                            output.textContent += '\\n👥 Расширенный круг:\\n';
                            msg.data.extended_circle.forEach(function(p) {
                                output.textContent += '  • ' + p.name + ' (' + p.relation + ', ' + (p.age || '?') + ' лет)';
                                if (p.description) {
                                    output.textContent += ' - ' + p.description;
                                }
                                output.textContent += '\\n';
                            });
                        }
                        
                    } else if (msg.event === 'day_result') {
                        output.textContent += '\\n==============================\\n';
                        output.textContent += '📅 ' + msg.data.date + ' (' + msg.data.day_context.day_of_week + ')\\n';
                        output.textContent += '💰 Потрачено: ' + Math.round(msg.data.day_summary.total_spent) + ' руб\\n';
                        output.textContent += '😊 Настроение: ' + msg.data.day_summary.mood_trajectory + '\\n';
                        
                        // Социальные взаимодействия
                        if (msg.data.social_interactions && msg.data.social_interactions.length > 0) {
                            output.textContent += '\\n👥 Социальные взаимодействия:\\n';
                            msg.data.social_interactions.forEach(function(si) {
                                output.textContent += '  • ' + si.with_person + ': ' + si.context + ' (' + si.emotional_impact + ')\\n';
                                
                                // Показываем несколько сообщений из чата
                                if (si.chat && si.chat.length > 0) {
                                    const maxMessages = Math.min(2, si.chat.length);
                                    for (let i = 0; i < maxMessages; i++) {
                                        const c = si.chat[i];
                                        output.textContent += '    💬 ' + c.from_person + ': ' + c.text + '\\n';
                                    }
                                    if (si.chat.length > 2) {
                                        output.textContent += '    ... (ещё ' + (si.chat.length - 2) + ' сообщений)\\n';
                                    }
                                }
                            });
                        }
                        
                        // Покупки
                        if (msg.data.transactions && msg.data.transactions.length > 0) {
                            output.textContent += '\\n🛒 Покупки:\\n';
                            msg.data.transactions.forEach(function(t) {
                                const itemsPreview = t.items.slice(0, 3).join(', ');
                                const moreItems = t.items.length > 3 ? ' и ещё ' + (t.items.length - 3) : '';
                                output.textContent += '  • ' + t.time + ' ' + t.place + ': ' + itemsPreview + moreItems + ' - ' + Math.round(t.amount) + ' руб (' + t.category + ')\\n';
                            });
                        }
                        
                        // Ключевые моменты
                        if (msg.data.day_summary.key_moments && msg.data.day_summary.key_moments.length > 0) {
                            output.textContent += '\\n✨ Ключевые моменты:\\n';
                            msg.data.day_summary.key_moments.forEach(function(moment) {
                                output.textContent += '  • ' + moment + '\\n';
                            });
                        }
                        
                    } else if (msg.event === 'complete') {
                        output.textContent += '\\n\\n✅ Симуляция завершена!\\n';
                        
                        // Краткая аналитика
                        if (msg.data.analysis && msg.data.analysis.insights) {
                            output.textContent += '\\n📊 Ключевые выводы:\\n';
                            msg.data.analysis.insights.forEach(function(insight) {
                                output.textContent += '  • ' + insight + '\\n';
                            });
                        }
                        
                        eventSource.close();
                        console.log('Simulation completed, closing connection');
                    }
                    
                    // Прокручиваем вниз
                    output.scrollTop = output.scrollHeight;
                    
                } catch (error) {
                    console.error('Error parsing message:', error);
                    output.textContent += '\\n❌ Ошибка обработки данных: ' + error.message + '\\n';
                }
            };
            
            eventSource.onerror = function(error) {
                console.error('EventSource error:', error);
                output.textContent += '\\n❌ Ошибка соединения. Проверьте консоль для деталей.\\n';
                eventSource.close();
            };
            
            return false;
        });
    });
})();
</script>

</body>
</html>
"""

def run_web_interface():
    """Запускает веб-интерфейс"""
    print("🚀 Запускаем веб-интерфейс...")
    print("📍 Откройте в браузере: http://localhost:5001")
    print("🛑 Для остановки нажмите Ctrl+C")
    app.run(debug=False, port=5001, host="0.0.0.0")


@app.route("/")
def index() -> str:
    """Вывод простой формы для запуска симуляции"""
    return render_template_string(FORM_HTML)


@app.route("/simulate", methods=["POST"])
def simulate_route():
    """Запускает симуляцию и возвращает результат"""
    person = Person(
        id=str(uuid4()),
        name=request.form.get("name", "Александр Петров"),
        age=int(request.form.get("age", 28)),
        gender=request.form.get("gender", "мужчина"),
        profession=request.form.get("profession", "менеджер"),
        income_level=request.form.get("income", "средний"),
        family_status=request.form.get("family_status", "не женат"),
        children=int(request.form.get("children", 0)),
        region=request.form.get("region", "Москва"),
        city_type=request.form.get("city_type", "мегаполис"),
        education=request.form.get("education"),
        employment=None,
        religion=request.form.get("religion"),
        ideology=request.form.get("ideology"),
        digital_literacy=request.form.get("digital_literacy"),
        context=request.form.get("context"),
        cognitive_frame=try_parse_json(request.form.get("cognitive_frame")),
        rhetorical_manner=try_parse_json(request.form.get("rhetorical_manner")),
        trigger_points=(
            try_parse_json(request.form.get("trigger_points"))
            if request.form.get("trigger_points", "").strip().startswith("[")
            else [tp.strip() for tp in request.form.get("trigger_points", "").split(",") if tp.strip()] if request.form.get("trigger_points") else None
        ),
        interpretation_biases=try_parse_json(request.form.get("interpretation_biases")),
        meta_self_view=try_parse_json(request.form.get("meta_self_view")),
        speech_profile=try_parse_json(request.form.get("speech_profile")),
        full_history=[HistoryEvent(**ev) for ev in try_parse_json(request.form.get("full_history")) or []] if request.form.get("full_history") else None,
    )
    days = int(request.form.get("days", 3))
    sd = request.form.get("start_date")
    if sd:
        start_date = datetime.strptime(sd, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=days - 1)
    config = SimulationConfig(
        target_person_id=person.id,
        start_date=start_date,
        days=days,
        memory_window=5,
    )

    simulator = LifeTransactionSimulator(config, [person])
    simulation_result = asyncio.run(simulator.run_simulation())
    return jsonify(simulation_result)


@app.route("/simulate_stream")
def simulate_stream_route():
    """Запускает симуляцию и стримит прогресс через SSE"""
    # Создаём персонажа
    person = Person(
        id=str(uuid4()),
        name=request.args.get("name", "Александр Петров"),
        age=int(request.args.get("age", 28)),
        gender=request.args.get("gender", "мужчина"),
        profession=request.args.get("profession", "менеджер"),
        income_level=request.args.get("income", "средний"),
        family_status=request.args.get("family_status", "не женат"),
        children=int(request.args.get("children", 0)),
        region=request.args.get("region", "Москва"),
        city_type=request.args.get("city_type", "мегаполис"),
        education=request.args.get("education"),
        employment=None,
        religion=request.args.get("religion"),
        ideology=request.args.get("ideology"),
        digital_literacy=request.args.get("digital_literacy"),
        context=request.args.get("context"),
        cognitive_frame=try_parse_json(request.args.get("cognitive_frame")),
        rhetorical_manner=try_parse_json(request.args.get("rhetorical_manner")),
        trigger_points=(
            try_parse_json(request.args.get("trigger_points"))
            if request.args.get("trigger_points", "").strip().startswith("[")
            else [tp.strip() for tp in request.args.get("trigger_points", "").split(",") if tp.strip()] if request.args.get("trigger_points") else None
        ),
        interpretation_biases=try_parse_json(request.args.get("interpretation_biases")),
        meta_self_view=try_parse_json(request.args.get("meta_self_view")),
        speech_profile=try_parse_json(request.args.get("speech_profile")),
        full_history=[HistoryEvent(**ev) for ev in try_parse_json(request.args.get("full_history")) or []] if request.args.get("full_history") else None,
    )
    
    days = int(request.args.get("days", 3))
    sd = request.args.get("start_date")
    if sd:
        start_date = datetime.strptime(sd, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=days - 1)
    config = SimulationConfig(
        target_person_id=person.id,
        start_date=start_date,
        days=days,
        memory_window=5,
    )

    simulator = LifeTransactionSimulator(config, [person])
    q = queue.Queue()

    def _json_safe(obj):
        """Безопасная сериализация в JSON"""
        return json.loads(json.dumps(obj, default=str, ensure_ascii=False))

    def progress(event_type, data):
        """Callback для прогресса симуляции"""
        print(f"Progress event: {event_type}")  # Для отладки
        
        # Конвертируем данные в JSON-safe формат
        if hasattr(data, "json"):
            data = json.loads(data.json())
        elif hasattr(data, "dict"):
            data = data.dict()
        
        data = _json_safe(data)
        q.put({"event": event_type, "data": data})

    async def run():
        """Запуск симуляции в отдельном потоке"""
        try:
            result = await simulator.run_simulation(progress_callback=progress)
            
            # Конвертируем результат
            if hasattr(result, "json"):
                result = json.loads(result.json())
            elif hasattr(result, "dict"):
                result = result.dict()
            
            result = _json_safe(result)
            q.put({"event": "complete", "data": result})
        except Exception as e:
            print(f"Error in simulation: {e}")
            import traceback
            traceback.print_exc()
            q.put({"event": "error", "data": {"message": str(e)}})

    # Запускаем симуляцию в отдельном потоке
    threading.Thread(target=lambda: asyncio.run(run()), daemon=True).start()

    def generate():
        """Генератор SSE событий"""
        while True:
            try:
                item = q.get(timeout=30)  # Таймаут 30 секунд
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                if item["event"] in ["complete", "error"]:
                    break
            except queue.Empty:
                # Отправляем heartbeat для поддержания соединения
                yield f"data: {json.dumps({'event': 'heartbeat'})}\n\n"

    return Response(
        stream_with_context(generate()), 
        mimetype="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # Для nginx
        }
    )

async def run_console_simulation(args):
    """Запускает симуляцию в консольном режиме"""
    # Создаем персону
    person = Person(
        id=str(uuid4()),
        name=args.name,
        age=args.age,
        gender=args.gender,
        profession=args.profession,
        income_level=args.income,
        family_status=args.family,
        children=args.children,
        region=args.region,
        city_type=args.city_type,
        education=args.education,
        employment=args.employment,
        religion=args.religion,
        ideology=args.ideology,
        digital_literacy=args.digital_literacy,
        context=args.context,
        cognitive_frame=try_parse_json(args.cognitive_frame),
        rhetorical_manner=try_parse_json(args.rhetorical_manner),
        trigger_points=(
            try_parse_json(args.trigger_points)
            if args.trigger_points and args.trigger_points.strip().startswith("[")
            else [tp.strip() for tp in args.trigger_points.split(",") if tp.strip()] if args.trigger_points else None
        ),
        interpretation_biases=try_parse_json(args.interpretation_biases),
        meta_self_view=try_parse_json(args.meta_self_view),
        speech_profile=try_parse_json(args.speech_profile),
        full_history=[HistoryEvent(**ev) for ev in try_parse_json(args.full_history) or []] if args.full_history else None,
    )
    
    print(f"\n👤 Персонаж: {person.name}, {person.age} лет, {person.profession}")
    print(f"📍 Локация: {person.city_type} {person.region}")
    print(f"💰 Доход: {person.income_level}")
    print(f"👨‍👩‍👧‍👦 Семья: {person.family_status}, детей: {person.children}")
    print(f"\n⏳ Симулируем {args.days} дней...\n")
    
    # Создаем конфигурацию
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        start_date = datetime.now() - timedelta(days=args.days-1)
    config = SimulationConfig(
        target_person_id=person.id,
        start_date=start_date,
        days=args.days,
        memory_window=5
    )
    
    # Подготовка callback для лайв-вывода
    def progress(event_type, data):
        if event_type == "environment":
            print("\n🔹 Социальное окружение:")
            for p in data.get("close_circle", []):
                print(f"  - {p['name']} ({p['relation']}, {p.get('age', '?')} лет)")
            for p in data.get("extended_circle", []):
                print(f"  - {p['name']} ({p['relation']}, {p.get('age', '?')} лет)")
        elif event_type == "day_result":
            from transaction_simulator.transaction_models import DailyResult
            result = data if isinstance(data, DailyResult) else DailyResult(**data)

            print(f"\n{'='*60}")
            print(f"📅 {result.date} ({result.day_context.day_of_week})")
            print(f"💰 Потрачено: {result.day_summary.total_spent} руб")
            print(f"😊 Настроение: {result.day_summary.mood_trajectory[:100]}...")

            print(f"\n👥 Социальные взаимодействия ({len(result.social_interactions)}):")
            for si in result.social_interactions:
                print(f"  - {si.with_person}: {si.context} ({si.emotional_impact})")
                if args.show_chats:
                    for msg in si.chat[:3]:
                        print(f"    💬 {msg.from_person}: {msg.text}")

            print(f"\n🛒 Покупки ({len(result.transactions)}):")
            for t in result.transactions:
                print(f"  - {t.time} {t.place}: {', '.join(t.items[:3])} - {t.amount} руб ({t.category})")

    # Запускаем симуляцию
    simulator = LifeTransactionSimulator(config, [person])
    simulation_result = await simulator.run_simulation(progress_callback=progress)

    # Извлекаем результаты
    results = simulation_result['daily_results']
    
    # Генерируем отчет
    if args.report:
        print(f"\n{'='*60}")
        print("📋 ДЕТАЛЬНЫЙ ОТЧЕТ")
        print('='*60)
        report_gen = ReportGenerator(person)
        
        # Конвертируем словари обратно в объекты для генератора отчета
        daily_results_objects = []
        for result_dict in results:
            from transaction_simulator.transaction_models import DailyResult
            daily_results_objects.append(DailyResult(**result_dict))
        
        report = report_gen.generate_detailed_report(daily_results_objects)
        print(report)
    
    # Сохраняем результаты
    if args.output:
        output_data = {
            'person': {
                'name': person.name,
                'age': person.age,
                'gender': person.gender,
                'profession': person.profession,
                'income_level': person.income_level,
                'family_status': person.family_status,
                'children': person.children,
                'region': person.region,
                'city_type': person.city_type
            },
            'simulation_date': datetime.now().isoformat(),
            'days_simulated': args.days,
            'results': results,  # Уже в формате словарей
            'analysis': simulation_result.get('analysis', {})  # Добавляем анализ если есть
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результаты сохранены в {args.output}")

def main():
    parser = argparse.ArgumentParser(
        description='Симулятор жизни человека',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

1. Запустить веб-интерфейс (рекомендуется):
   python run_simulator.py --web

2. Консольная симуляция с параметрами по умолчанию:
   python run_simulator.py

3. Симуляция подростка:
   python run_simulator.py --name "Маша" --age 16 --gender "женщина" --profession "школьница"

4. Симуляция с отчетом и сохранением:
   python run_simulator.py --days 7 --report --output results.json

5. Подробная симуляция с чатами:
   python run_simulator.py --show-chats --report
"""
    )
    
    # Режим работы
    parser.add_argument('--web', action='store_true', 
                       help='Запустить веб-интерфейс (рекомендуется)')
    
    # Параметры персонажа
    parser.add_argument('--name', default='Александр Петров',
                       help='Имя персонажа')
    parser.add_argument('--age', type=int, default=28,
                       help='Возраст (14-80)')
    parser.add_argument('--gender', choices=['мужчина', 'женщина'], 
                       default='мужчина', help='Пол')
    parser.add_argument('--profession', default='менеджер',
                       help='Профессия')
    parser.add_argument('--income', choices=['низкий', 'средний', 'высокий'],
                       default='средний', help='Уровень дохода')
    parser.add_argument('--family', default='не женат',
                       help='Семейное положение')
    parser.add_argument('--children', type=int, default=0,
                       help='Количество детей')
    parser.add_argument('--region', default='Москва',
                       help='Регион проживания')
    parser.add_argument('--city-type', 
                       choices=['село', 'малый город', 'средний город', 
                               'крупный город', 'мегаполис'],
                       default='мегаполис', help='Тип населенного пункта')
    parser.add_argument('--interests', default='',
                       help='Интересы через запятую')
    parser.add_argument('--traits', default='',
                       help='Черты характера через запятую')
    parser.add_argument('--education', help='Образование')
    parser.add_argument('--employment', help='Профессия')
    parser.add_argument('--religion', help='Религия')
    parser.add_argument('--ideology', help='Идеологические взгляды')
    parser.add_argument('--digital-literacy', dest='digital_literacy',
                       help='Цифровая грамотность')
    parser.add_argument('--context', help='Бытовой контекст')
    parser.add_argument('--cognitive-frame', dest='cognitive_frame',
                       help='Когнитивная рамка (JSON)')
    parser.add_argument('--rhetorical-manner', dest='rhetorical_manner',
                       help='Риторическая манера (JSON)')
    parser.add_argument('--trigger-points', dest='trigger_points',
                       help='Триггерные точки (JSON или список через запятую)')
    parser.add_argument('--interpretation-biases', dest='interpretation_biases',
                       help='Когнитивные искажения (JSON)')
    parser.add_argument('--meta-self-view', dest='meta_self_view',
                       help='Взгляд на себя (JSON)')
    parser.add_argument('--speech-profile', dest='speech_profile',
                       help='Речевой профиль (JSON)')
    parser.add_argument('--full-history', dest='full_history',
                       help='Дополнительные факты (JSON список событий)')
    
    # Параметры симуляции
    parser.add_argument('--days', type=int, default=3,
                       help='Количество дней для симуляции (1-30)')
    parser.add_argument('--start-date',
                       help='Дата начала симуляции YYYY-MM-DD')
    parser.add_argument('--show-chats', action='store_true',
                       help='Показывать диалоги')
    parser.add_argument('--report', action='store_true',
                       help='Генерировать детальный отчет')
    parser.add_argument('--output', help='Файл для сохранения результатов')
    
    args = parser.parse_args()
    
    if args.web:
        run_web_interface()
    else:
        # Запускаем консольную симуляцию
        asyncio.run(run_console_simulation(args))

if __name__ == '__main__':
    main()