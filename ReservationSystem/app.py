from flask import Flask, render_template, request, redirect, url_for
import csv

app = Flask(__name__)

# CSV 파일 경로
TRAINS_CSV = 'static/trains.csv'
RESERVATIONS_CSV = 'static/reservations.csv'

def read_reservations():
    """reservations.csv 파일에서 예약 데이터를 읽어옴."""
    reservations = []
    try:
        with open(RESERVATIONS_CSV, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                reservations.append({
                    "train_no": row.get("train_no", ""),
                    "date": row.get("date", ""),
                    "departure": row.get("departure", ""),
                    "arrival": row.get("arrival", ""),
                    "time": row.get("time", "")
                })
    except FileNotFoundError:
        pass  # 파일이 없으면 빈 리스트 반환

    reservations = sorted(reservations, key=lambda x: (x['date'], x['departure'], x['arrival'], x['time']))
    return reservations

# 특정 조건에 맞는 기차 필터링
def filter_trains(departure, arrival, date):
    all_trains = read_trains()
    return [train for train in all_trains if train['departure'] == departure and train['arrival'] == arrival and train['date'] == date]

# 예약 데이터 읽기
def read_trains():
    """trains.csv 파일에서 데이터를 읽고 정렬."""
    trains = []
    try:
        with open(TRAINS_CSV, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                trains.append(row)
    except FileNotFoundError:
        pass

    # (날짜, departure, arrival, time) 기준으로 정렬
    trains = sorted(trains, key=lambda x: (x['date'], x['departure'], x['arrival'], x['time']))
    return trains


# 예약 데이터 추가
def add_reservation(data):
    with open(RESERVATIONS_CSV, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select', methods=['GET', 'POST'])
def select_train():
    locations = get_unique_locations()  # 출발지 및 도착지 목록 가져오기
    if request.method == 'POST':
        departure = request.form['departure']
        arrival = request.form['arrival']
        date = request.form['date']
        filtered_trains = filter_trains(departure, arrival, date)
        return render_template('filtered_trains.html', trains=filtered_trains, departure=departure, arrival=arrival, date=date)
    return render_template('select_train.html', locations=locations)


@app.route('/reserve', methods=['POST'])
def reserve_train():
    train_no = request.form['train_no']
    date = request.form['date']
    departure = request.form['departure']
    arrival = request.form['arrival']
    time = request.form['time']
    add_reservation([train_no, date, departure, arrival, time])
    return redirect(url_for('reservations'))


@app.route('/reservations')
def reservations():
    reservations = read_reservations()
    return render_template('reservations.html', reservations=reservations)

@app.route('/delete/<int:reservation_index>', methods=['POST'])
def delete(reservation_index):
    reservations = read_reservations()
    if 0 <= reservation_index < len(reservations):
        del reservations[reservation_index]
        save_reservations(reservations)
    return redirect(url_for('reservations'))

@app.route('/change/<int:reservation_index>', methods=['GET', 'POST'])
def change(reservation_index):
    reservations = read_reservations()
    trains = read_trains()
    reservation = reservations[reservation_index]

    if request.method == 'POST':
        selected_train = request.form['train']
        train_no, date, time, departure, arrival = selected_train.split(',')
        reservations[reservation_index] = {
            "train_no": train_no,
            "date": date,
            "departure": departure,
            "arrival": arrival,
            "time": time,
        }
        save_reservations(reservations)
        return redirect(url_for('reservations'))

    return render_template('change_reservation.html', reservation=reservation, trains=trains)

def save_reservations(data):
    with open(RESERVATIONS_CSV, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["train_no", "date", "departure", "arrival", "time"])
        writer.writeheader()
        writer.writerows(data)

@app.route('/view_all', methods=['GET'])
def view_all_trains():
    return render_template('view_all_trains.html')

@app.route('/api/trains', methods=['GET'])
def get_trains():
    """모든 기차 목록을 JSON으로 반환."""
    trains = read_trains()
    trains = sorted(trains, key=lambda x: (x['date'], x['departure'], x['arrival'], x['time']))  # 확실한 정렬
    page = int(request.args.get('page', 1))
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "trains": trains[start:end],
        "has_more": end < len(trains)  # 다음 페이지 여부
    }


def get_unique_locations():
    """trains.csv에서 모든 출발지와 도착지를 추출."""
    locations = set()
    try:
        with open(TRAINS_CSV, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                locations.add(row['departure'])
                locations.add(row['arrival'])
    except FileNotFoundError:
        pass
    return sorted(locations)



if __name__ == '__main__':
    # 예약 CSV 초기화 (파일 없을 때 생성)
    try:
        with open(RESERVATIONS_CSV, 'x') as file:
            writer = csv.writer(file)
            writer.writerow(['train_no', 'date', 'departure', 'arrival', 'time', 'details'])
    except FileExistsError:
        pass
    app.run(debug=True)