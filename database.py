import json
import os
import threading

# 使用线程锁防止文件并发读写冲突
file_lock = threading.Lock()

BASE_DATA_DIR = "data"
STUDENTS_DIR = os.path.join(BASE_DATA_DIR, "students")
TEACHERS_DIR = os.path.join(BASE_DATA_DIR, "teachers")

# 确保目录存在
os.makedirs(STUDENTS_DIR, exist_ok=True)
os.makedirs(TEACHERS_DIR, exist_ok=True)

class Database:
    @staticmethod
    def get_student_path(student_id):
        return os.path.join(STUDENTS_DIR, f"{student_id}.json")

    @staticmethod
    def read_student(student_id):
        path = Database.get_student_path(student_id)
        with file_lock:
            if not os.path.exists(path):
                return None
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保包含必要的数组字段
                    if "weakness_log" not in data:
                        data["weakness_log"] = []
                    return data
            except Exception as e:
                print(f"读取学生档案失败: {e}")
                return None

    @staticmethod
    def write_student(student_id, data):
        path = Database.get_student_path(student_id)
        with file_lock:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"写入学生档案失败: {e}")
                return False

    @staticmethod
    def list_all_students():
        students = []
        with file_lock:
            if not os.path.exists(STUDENTS_DIR):
                return []
            for filename in os.listdir(STUDENTS_DIR):
                if filename.endswith(".json"):
                    student_id = filename.replace(".json", "")
                    # 内部直接读取逻辑，避免嵌套锁
                    path = os.path.join(STUDENTS_DIR, filename)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            students.append({
                                "id": student_id,
                                "name": data.get("basic_info", {}).get("name", "未知")
                            })
                    except:
                        continue
        return students

    @staticmethod
    def create_student(student_id, name, tags=None):
        if Database.read_student(student_id):
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
        success = Database.write_student(student_id, new_student)
        return success, "创建成功" if success else "存储失败"
