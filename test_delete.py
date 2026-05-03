import unittest
import os
import shutil
from database.manager import DatabaseManager

class TestStudentManagement(unittest.TestCase):
    def setUp(self):
        # 创建临时测试环境
        self.test_dir = "test_data"
        self.db = DatabaseManager(base_dir=self.test_dir)
        self.test_sid = "TEST001"
        self.db.create_student(self.test_sid, "测试生")

    def tearDown(self):
        # 清理测试环境
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists("logs"):
            shutil.rmtree("logs")

    def test_delete_success(self):
        """测试删除已存在的学生档案"""
        success, msg = self.db.delete_student(self.test_sid)
        self.assertTrue(success)
        self.assertIsNone(self.db.read_student(self.test_sid))

    def test_delete_non_existent(self):
        """测试删除不存在的学生档案"""
        success, msg = self.db.delete_student("NON_EXISTENT")
        self.assertFalse(success)
        self.assertEqual(msg, "档案不存在")

    def test_operation_logging(self):
        """验证删除操作是否记录到日志"""
        self.db.delete_student(self.test_sid, operator="ADMIN_TEST")
        log_path = os.path.join("logs", "operations.log")
        self.assertTrue(os.path.exists(log_path))
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("ACTION:DELETE", content)
            self.assertIn("TARGET:TEST001", content)

if __name__ == "__main__":
    unittest.main()
