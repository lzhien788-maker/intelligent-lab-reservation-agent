-- 智能实验室预约系统 数据库初始化脚本
-- 由 backend/scripts/export_db.py 自动生成
-- 导入方式：mysql -u root -p < lab_agent.sql  或 Navicat 里“运行 SQL 文件”

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `lab_agent` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `lab_agent`;

-- ---------------- users ----------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号',
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号',
  `role` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色: student-学生, admin-管理员',
  `email` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手机号',
  `status` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '状态: 0-禁用，1-正常',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  `avatar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '头像地址',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户信息表';

INSERT INTO `users` (`username`, `password`, `name`, `role`, `email`, `phone`, `status`, `id`, `create_time`, `update_time`, `avatar`) VALUES ('admin', '$2b$12$u21vhiU7EY/yuHkhcrBs8eBxtPiKm4Po0ytVx4iub0EMHzvLqmvAa', 'zqp', 'admin', 'admin@test.com', '15917007733', '1', 1, '2026-11-03T17:31:56', '2026-11-07T12:50:45', '/uploads/1794027044324_4a72bbe4.jpg');
INSERT INTO `users` (`username`, `password`, `name`, `role`, `email`, `phone`, `status`, `id`, `create_time`, `update_time`, `avatar`) VALUES ('aaa', '$2b$12$.0pe//EdNITGkBeqD6Ph8OMYbxjPR80D97tkLlFKNeVEeXKav6sBu', 'aaa', 'student', NULL, NULL, '1', 2, '2026-11-04T23:26:15', '2026-11-04T23:26:15', NULL);
INSERT INTO `users` (`username`, `password`, `name`, `role`, `email`, `phone`, `status`, `id`, `create_time`, `update_time`, `avatar`) VALUES ('111', '$2b$12$Rdvg9miq688DFHL0RJDsCO7in80LpvBXG4cIkxFwWZ7JvcR6QUEXS', 'zqq', 'student', '18075203@qq.com', '15220642222', '1', 7, '2026-11-06T16:34:26', '2026-11-06T16:36:53', NULL);

-- ---------------- labs ----------------
DROP TABLE IF EXISTS `labs`;
CREATE TABLE `labs` (
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '名称',
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '简介',
  `img` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '封面',
  `location` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '位置',
  `capacity` int NOT NULL COMMENT '容量',
  `open_time` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开放开始时间',
  `close_time` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开放结束时间',
  `status` int NOT NULL COMMENT '状态, 0-关闭, 1-开放',
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实验室信息';

INSERT INTO `labs` (`name`, `description`, `img`, `location`, `capacity`, `open_time`, `close_time`, `status`, `id`, `create_time`, `update_time`) VALUES ('计算机实验室', '计算机实验室', '/uploads/lab_computer.jpg', '综合实验楼102', 20, '09:00', '15:00', 1, 1, '2026-11-07T12:36:27', '2026-11-08T14:57:46');
INSERT INTO `labs` (`name`, `description`, `img`, `location`, `capacity`, `open_time`, `close_time`, `status`, `id`, `create_time`, `update_time`) VALUES ('物理实验室', '物理实验室', '/uploads/lab_physics.jpg', '综合实验楼101', 20, '08:00', '18:00', 1, 2, '2026-11-07T12:48:28', '2026-11-08T14:57:46');
INSERT INTO `labs` (`name`, `description`, `img`, `location`, `capacity`, `open_time`, `close_time`, `status`, `id`, `create_time`, `update_time`) VALUES ('电子实验室', '电子实验室', '/uploads/lab_electronics.jpg', '综合实验楼201', 20, '08:00', '18:00', 1, 5, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `labs` (`name`, `description`, `img`, `location`, `capacity`, `open_time`, `close_time`, `status`, `id`, `create_time`, `update_time`) VALUES ('化学实验室', '化学实验室', '/uploads/lab_chemistry.jpg', '综合实验楼301', 20, '08:00', '18:00', 1, 6, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `labs` (`name`, `description`, `img`, `location`, `capacity`, `open_time`, `close_time`, `status`, `id`, `create_time`, `update_time`) VALUES ('生物实验室', '生物实验室', '/uploads/lab_biology.jpg', '综合实验楼302', 20, '08:00', '18:00', 1, 7, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `labs` (`name`, `description`, `img`, `location`, `capacity`, `open_time`, `close_time`, `status`, `id`, `create_time`, `update_time`) VALUES ('人工智能实验室', '人工智能实验室', '/uploads/lab_ai.jpg', '综合实验楼401', 30, '08:00', '18:00', 1, 8, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `labs` (`name`, `description`, `img`, `location`, `capacity`, `open_time`, `close_time`, `status`, `id`, `create_time`, `update_time`) VALUES ('机器人实验室', '机器人实验室', '/uploads/lab_robotics.jpg', '综合实验楼402', 20, '09:00', '17:00', 1, 9, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `labs` (`name`, `description`, `img`, `location`, `capacity`, `open_time`, `close_time`, `status`, `id`, `create_time`, `update_time`) VALUES ('软件工程实验室', '软件工程实验室', '/uploads/lab_software.jpg', '综合实验楼501', 40, '08:00', '20:00', 1, 10, '2026-11-08T14:57:46', '2026-11-08T14:57:46');

-- ---------------- equipments ----------------
DROP TABLE IF EXISTS `equipments`;
CREATE TABLE `equipments` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `lab_id` int NOT NULL COMMENT '所属实验室ID',
  `name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '设备名称',
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '说明',
  `img` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '图片',
  `spec` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '型号规格',
  `quantity` int NOT NULL COMMENT '数量',
  `status` int NOT NULL COMMENT '状态：0-维修，1-正常',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `lab_id` (`lab_id`),
  CONSTRAINT `equipments_ibfk_1` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实验室设备表';

INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (1, 2, '大炮', '111', '/uploads/1794031037810_60cb7467.jpg', 'cx-290', 7, 1, '2026-11-07T13:57:26', '2026-11-07T13:57:26');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (2, 1, '飞机', '111', NULL, 'cx-299', 5, 0, '2026-11-07T13:57:48', '2026-11-07T13:57:48');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (4, 1, 'RTX4090', '深度学习训练显卡', NULL, '24G 显存', 2, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (5, 1, '开发主机', '学生上机编程', NULL, 'i7 / 32G / 1T SSD', 20, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (6, 1, '投影仪', '授课演示', NULL, '1080P', 1, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (7, 1, '千兆交换机', '机房组网', NULL, '24 口', 1, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (8, 5, '示波器', '电路波形观测', NULL, '100MHz 双通道', 8, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (9, 5, '信号发生器', '信号源实验', NULL, 'DDS 60MHz', 6, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (10, 5, '数字万用表', '电子测量', NULL, '4 位半', 10, 0, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (11, 5, '直流稳压电源', '电路供电', NULL, '30V 5A', 8, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (12, 2, '光学实验台', '几何光学实验', NULL, '1.2m 隔振台', 3, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (13, 2, '氦氖激光器', '干涉衍射实验', NULL, '632.8nm', 2, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (14, 2, '力学轨道', '牛顿定律实验', NULL, '气垫导轨 1.5m', 3, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (15, 2, '分光计', '光谱测量', NULL, '0.1° 精度', 4, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (16, 6, '电子天平', '试剂称量', NULL, '0.1mg', 4, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (17, 6, '离心机', '样品分离', NULL, '4000rpm', 2, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (18, 6, '通风橱', '有机实验', NULL, '1.5m', 2, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (19, 6, 'pH计', '溶液酸碱度', NULL, '0.01pH', 4, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (20, 7, '显微镜', '细胞观察', NULL, '1000x 光学', 10, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (21, 7, '恒温培养箱', '菌种培养', NULL, '室温 ~ 60℃', 2, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (22, 7, '移液器', '微量取样', NULL, '0.5-10μL', 20, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (23, 7, 'PCR仪', '基因扩增', NULL, '96 孔', 1, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (24, 8, 'GPU训练服务器', '大模型微调', NULL, '2*RTX4090 / 128G', 1, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (25, 8, '深度相机', '视觉数据采集', NULL, 'RealSense D435i', 3, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (26, 8, '标注工作站', '数据集标注', NULL, 'i9 / 64G', 6, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (27, 8, 'Livox激光雷达', 'SLAM 建模', NULL, 'Mid-360', 3, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (28, 9, 'URS机械臂', '工业机械臂教学', NULL, '负载 5kg', 2, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (29, 9, '深度相机', '视觉抓取', NULL, 'RealSense D435i', 4, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');
INSERT INTO `equipments` (`id`, `lab_id`, `name`, `description`, `img`, `spec`, `quantity`, `status`, `create_time`, `update_time`) VALUES (30, 10, '开发工作站', '前后端联调', NULL, 'i9 / 64G', 40, 1, '2026-11-08T14:57:46', '2026-11-08T14:57:46');

-- ---------------- reservations ----------------
DROP TABLE IF EXISTS `reservations`;
CREATE TABLE `reservations` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` int NOT NULL COMMENT '预约人',
  `lab_id` int NOT NULL COMMENT '预约的实验室',
  `equipment_id` int DEFAULT NULL COMMENT '预约的设备, 空表示只约实验室',
  `reserve_date` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '预约日期',
  `start_time` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '开始时间',
  `end_time` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '结束时间',
  `remark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注',
  `status` int NOT NULL COMMENT '预约状态 0待审核 1已通过 2已拒绝 3已取消',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `lab_id` (`lab_id`),
  KEY `equipment_id` (`equipment_id`),
  CONSTRAINT `reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `reservations_ibfk_2` FOREIGN KEY (`lab_id`) REFERENCES `labs` (`id`),
  CONSTRAINT `reservations_ibfk_3` FOREIGN KEY (`equipment_id`) REFERENCES `equipments` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预约信息';

-- reservations：只建表，不插入数据

SET FOREIGN_KEY_CHECKS = 1;
