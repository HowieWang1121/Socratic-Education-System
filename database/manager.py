import json
import os
import threading
import datetime

# 递归锁，允许同一线程多次获取
file_lock = threading.RLock()

class DatabaseManager:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
        self.students_dir = os.path.join(base_dir, "students")
        self.logs_dir = os.path.join(os.path.dirname(base_dir), "logs")
        os.makedirs(self.students_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def _log_operation(self, user, action, target_id, details=""):
        log_file = os.path.join(self.logs_dir, "operations.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] USER:{user} ACTION:{action} TARGET:{target_id} DETAILS:{details}\n"
        with file_lock:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)

    def get_student_path(self, student_id):
        return os.path.join(self.students_dir, f"{student_id}.json")

    def read_student(self, student_id):
        path = self.get_student_path(student_id)
        with file_lock:
            if not os.path.exists(path):
                return None
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Read error: {e}")
                return None

    def write_student(self, student_id, data, operator="SYSTEM"):
        path = self.get_student_path(student_id)
        with file_lock:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self._log_operation(operator, "WRITE/UPDATE", student_id)
                return True
            except Exception as e:
                print(f"Write error: {e}")
                return False

    def create_student(self, student_id, name, tags=None, operator="TEACHER"):
        if self.read_student(student_id):
            return False, "学号已存在"
        
        new_student = {
            "basic_info": {
                "name": name,
                "student_id": student_id,
                "tags": tags or ["新入库"]
            },
            "cognitive_profile": {
                "learning_style": "未知",
                "concentration_level": "中等",
                "thinking_habits": "待分析"
            },
            "subject_weaknesses": [],
            "weakness_log": [],
            "historical_evaluations": []
        }
        success = self.write_student(student_id, new_student, operator=operator)
        return success, "创建成功" if success else "存储失败"

    def delete_student(self, student_id, operator="TEACHER"):
        path = self.get_student_path(student_id)
        with file_lock:
            if not os.path.exists(path):
                return False, "档案不存在"
            try:
                os.remove(path)
                self._log_operation(operator, "DELETE", student_id, "Permanent deletion")
                return True, "删除成功"
            except Exception as e:
                return False, f"删除失败: {str(e)}"

    def list_students(self):
        students = []
        with file_lock:
            if not os.path.exists(self.students_dir):
                return []
            for filename in os.listdir(self.students_dir):
                if filename.endswith(".json"):
                    sid = filename.replace(".json", "")
                    path = os.path.join(self.students_dir, filename)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            students.append({
                                "id": sid,
                                "name": data.get("basic_info", {}).get("name", "Unknown")
                            })
                    except: continue
        return students
