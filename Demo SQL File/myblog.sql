-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 02, 2020 at 04:43 PM
-- Server version: 10.4.11-MariaDB
-- PHP Version: 7.4.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `myblog`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `id` int(11) NOT NULL,
  `name` varchar(80) NOT NULL,
  `username` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password` varchar(200) NOT NULL,
  `profile` varchar(180) DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `activate` tinyint(1) NOT NULL,
  `twostep` tinyint(1) NOT NULL,
  `darkmode` tinyint(1) NOT NULL,
  `apikey` varchar(120) NOT NULL
) ;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`id`, `name`, `username`, `email`, `password`, `profile`, `date`, `activate`, `twostep`, `darkmode`, `apikey`) VALUES
(1, 'abc', 'abc', 'abc@gmail.com', '$2b$12$qkeA2aZsRRUuKViFBA94SO6zATAVhkiuAQkCrQ2GMgn4ZSGVcyii.', 'b40272c4d2c789181846c13a31.png', '2020-08-02 19:49:02', 1, 0, 0, '8e1215994266e4261df081818c691241f8'),
(2, 'def', 'def', 'def@gmail.com', '$2b$12$bseS0h2T2xeIESzq9.u/w.C/XQrMc72jLr4AfQVivA0GZ.ctP8wzC', 'profile.jpg', '2020-08-02 19:49:03', 1, 0, 0, 'e2c0a19479b9edbc5a0be182ccdef36e4d');

-- --------------------------------------------------------

--
-- Table structure for table `admincode`
--

CREATE TABLE `admincode` (
  `id` int(11) NOT NULL,
  `code` varchar(100) NOT NULL,
  `date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `admincode`
--

INSERT INTO `admincode` (`id`, `code`, `date`) VALUES
(1, 'admincode', '2020-08-02 19:49:01');

-- --------------------------------------------------------

--
-- Table structure for table `admin_to_all_users`
--

CREATE TABLE `admin_to_all_users` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) NOT NULL,
  `subject` varchar(6000) NOT NULL,
  `message` varchar(6000) NOT NULL,
  `date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `admin_to_all_users`
--

INSERT INTO `admin_to_all_users` (`id`, `admin_id`, `subject`, `message`, `date`) VALUES
(1, 1, 'To All Users', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique.', '2020-08-02 19:58:58');

-- --------------------------------------------------------

--
-- Table structure for table `admin_to_user`
--

CREATE TABLE `admin_to_user` (
  `id` int(11) NOT NULL,
  `admin_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `subject` varchar(6000) NOT NULL,
  `message` varchar(6000) NOT NULL,
  `date` datetime DEFAULT NULL,
  `read` tinyint(1) NOT NULL
) ;

--
-- Dumping data for table `admin_to_user`
--

INSERT INTO `admin_to_user` (`id`, `admin_id`, `user_id`, `subject`, `message`, `date`, `read`) VALUES
(1, 1, 1, 'To GHI', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique.', '2020-08-02 19:59:17', 0);

-- --------------------------------------------------------

--
-- Table structure for table `authors`
--

CREATE TABLE `authors` (
  `id` int(11) NOT NULL,
  `name` varchar(80) NOT NULL,
  `username` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `profile` varchar(180) DEFAULT NULL,
  `date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `authors`
--

INSERT INTO `authors` (`id`, `name`, `username`, `email`, `profile`, `date`) VALUES
(1, 'abc', 'abc', 'abc@gmail.com', 'b40272c4d2c789181846c13a31.png', '2020-08-02 19:49:02'),
(2, 'ghi', 'ghi', 'ghi@gmail.com', '44dca6f897fac1b5b46a35a230.png', '2020-08-02 19:49:02'),
(3, 'def', 'def', 'def@gmail.com', 'profile.jpg', '2020-08-02 19:49:03'),
(4, 'jkl', 'jkl', 'jkl@gmail.com', 'profile.jpg', '2020-08-02 19:49:03');

-- --------------------------------------------------------

--
-- Table structure for table `blogpost`
--

CREATE TABLE `blogpost` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `slug` varchar(200) NOT NULL,
  `body` varchar(6000) NOT NULL,
  `category_id` int(11) NOT NULL,
  `image` varchar(150) NOT NULL,
  `user_id` int(11) NOT NULL,
  `views` int(11) NOT NULL,
  `date_pub` datetime DEFAULT NULL,
  `rough_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `blogpost`
--

INSERT INTO `blogpost` (`id`, `title`, `slug`, `body`, `category_id`, `image`, `user_id`, `views`, `date_pub`, `rough_id`) VALUES
(1, 'My First Post', 'first-post', '<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique. Donec nec porta magna. In hac habitasse platea dictumst. Proin nunc tortor, elementum quis mauris vitae, efficitur aliquet ligula. Quisque ac ligula sit amet erat pharetra semper eget sit amet felis. Proin semper pellentesque dui sed consequat. Nam viverra nulla et ex consectetur mattis. Integer sed fermentum elit. Sed quam est, accumsan ac purus eget, lacinia venenatis augue. In scelerisque posuere quam sed suscipit. Nunc ac fringilla elit. Quisque eget sodales leo. Cras placerat laoreet tellus.</p>\r\n', 1, '52f8a47b42275b8084f4c88fdd.png', 2, 2, '2020-08-02 20:02:18', 1);

-- --------------------------------------------------------

--
-- Table structure for table `bugreport`
--

CREATE TABLE `bugreport` (
  `id` int(11) NOT NULL,
  `sub_date` datetime DEFAULT NULL,
  `submitted_by` varchar(100) NOT NULL,
  `email` varchar(120) NOT NULL,
  `title` varchar(120) NOT NULL,
  `bug_desc` varchar(120) NOT NULL,
  `bug_url` varchar(120) NOT NULL,
  `platform` varchar(80) NOT NULL,
  `browser` varchar(80) NOT NULL,
  `bug_date` varchar(120) NOT NULL,
  `scrnshot` varchar(80) DEFAULT NULL,
  `expected_res` varchar(120) DEFAULT NULL,
  `actual_res` varchar(120) DEFAULT NULL,
  `frequency` varchar(80) NOT NULL,
  `priority` varchar(80) NOT NULL,
  `status` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `bugreport`
--

INSERT INTO `bugreport` (`id`, `sub_date`, `submitted_by`, `email`, `title`, `bug_desc`, `bug_url`, `platform`, `browser`, `bug_date`, `scrnshot`, `expected_res`, `actual_res`, `frequency`, `priority`, `status`) VALUES
(1, '2020-08-02 20:07:42', 'John Doe', 'john@john.com', 'This is a Bug Title', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer ipsum mauris, interdum tristique rhoncus at, eleifend s', 'https://www.john.com', 'Mobile', 'Chrome', '02/08/2020', '0d650fd5d0feb5bf3cf2eb5480.jpg', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.', 'HARDLY EVER', 'HIGH', 0);

-- --------------------------------------------------------

--
-- Table structure for table `category`
--

CREATE TABLE `category` (
  `id` int(11) NOT NULL,
  `name` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `category`
--

INSERT INTO `category` (`id`, `name`) VALUES
(2, 'food'),
(1, 'travel'),
(3, 'vlog');

-- --------------------------------------------------------

--
-- Table structure for table `contact`
--

CREATE TABLE `contact` (
  `sno` int(11) NOT NULL,
  `name` varchar(80) NOT NULL,
  `email` varchar(50) NOT NULL,
  `website` varchar(120) NOT NULL,
  `message` varchar(6000) NOT NULL,
  `date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `contact`
--

INSERT INTO `contact` (`sno`, `name`, `email`, `website`, `message`, `date`) VALUES
(1, 'John Doe', 'john@john.com', 'https://www.john.com', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique. Donec nec porta magna. In hac habitasse platea dictumst. Proin nunc tortor, elementum quis mauris vitae, efficitur aliquet ligula. Quisque ac ligula sit amet erat pharetra semper eget sit amet felis. Proin semper pellentesque dui sed consequat. Nam viverra nulla et ex consectetur mattis. Integer sed fermentum elit. Sed quam est, accumsan ac purus eget, lacinia venenatis aug', '2020-08-02 19:51:23'),
(2, 'Jane Doe', 'jane@jane.com', 'https://www.jane.com', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique. Donec nec porta magna. In hac habitasse platea dictumst. Proin nunc tortor, elementum quis mauris vitae, efficitur aliquet ligula. Quisque ac ligula sit amet erat pharetra semper eget sit amet felis. Proin semper pellentesque dui sed consequat. Nam viverra nulla et ex consectetur mattis. Integer sed fermentum elit. Sed quam est, accumsan ac purus eget, lacinia venenatis aug', '2020-08-02 19:52:56');

-- --------------------------------------------------------

--
-- Table structure for table `posts`
--

CREATE TABLE `posts` (
  `id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `slug` varchar(200) NOT NULL,
  `body` varchar(6000) NOT NULL,
  `category_id` int(11) NOT NULL,
  `image` varchar(150) NOT NULL,
  `user_id` int(11) NOT NULL,
  `date_pub` datetime DEFAULT NULL,
  `draft` tinyint(1) NOT NULL,
  `status` int(11) DEFAULT NULL,
  `fair_id` int(11) DEFAULT NULL
) ;

--
-- Dumping data for table `posts`
--

INSERT INTO `posts` (`id`, `title`, `slug`, `body`, `category_id`, `image`, `user_id`, `date_pub`, `draft`, `status`, `fair_id`) VALUES
(1, 'My First Post', 'first-post', '<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique. Donec nec porta magna. In hac habitasse platea dictumst. Proin nunc tortor, elementum quis mauris vitae, efficitur aliquet ligula. Quisque ac ligula sit amet erat pharetra semper eget sit amet felis. Proin semper pellentesque dui sed consequat. Nam viverra nulla et ex consectetur mattis. Integer sed fermentum elit. Sed quam est, accumsan ac purus eget, lacinia venenatis augue. In scelerisque posuere quam sed suscipit. Nunc ac fringilla elit. Quisque eget sodales leo. Cras placerat laoreet tellus.</p>\r\n', 1, '52f8a47b42275b8084f4c88fdd.png', 2, '2020-08-02 20:00:37', 0, 1, 1),
(2, 'My Second Post', 'second-post', '<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique. Donec nec porta magna. In hac habitasse platea dictumst. Proin nunc tortor, elementum quis mauris vitae, efficitur aliquet ligula. Quisque ac ligula sit amet erat pharetra semper eget sit amet felis. Proin semper pellentesque dui sed consequat. Nam viverra nulla et ex consectetur mattis. Integer sed fermentum elit. Sed quam est, accumsan ac purus eget, lacinia venenatis augue. In scelerisque posuere quam sed suscipit. Nunc ac fringilla elit. Quisque eget sodales leo. Cras placerat laoreet tellus.</p>\r\n', 2, 'b517b46caa5241e0536631257b.png', 2, '2020-08-02 20:01:16', 1, 0, NULL),
(3, 'My Third Post', 'third-post', '<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique. Donec nec porta magna. In hac habitasse platea dictumst. Proin nunc tortor, elementum quis mauris vitae, efficitur aliquet ligula. Quisque ac ligula sit amet erat pharetra semper eget sit amet felis. Proin semper pellentesque dui sed consequat. Nam viverra nulla et ex consectetur mattis. Integer sed fermentum elit. Sed quam est, accumsan ac purus eget, lacinia venenatis augue. In scelerisque posuere quam sed suscipit. Nunc ac fringilla elit. Quisque eget sodales leo. Cras placerat laoreet tellus.</p>\r\n', 3, '962eb8b54a42b3f36743f15136.png', 2, '2020-08-02 20:01:45', 0, NULL, NULL),
(4, 'My Fourth Post', 'fourth-post', '<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique. Donec nec porta magna. In hac habitasse platea dictumst. Proin nunc tortor, elementum quis mauris vitae, efficitur aliquet ligula. Quisque ac ligula sit amet erat pharetra semper eget sit amet felis. Proin semper pellentesque dui sed consequat. Nam viverra nulla et ex consectetur mattis. Integer sed fermentum elit. Sed quam est, accumsan ac purus eget, lacinia venenatis augue. In scelerisque posuere quam sed suscipit. Nunc ac fringilla elit. Quisque eget sodales leo. Cras placerat laoreet tellus.</p>\r\n', 2, 'd8a575629d47d9a9984720e36a.png', 2, '2020-08-02 20:03:06', 1, NULL, NULL),
(5, 'My Demo Post', 'demo-post', '<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique. Donec nec porta magna. In hac habitasse platea dictumst. Proin nunc tortor, elementum quis mauris vitae, efficitur aliquet ligula. Quisque ac ligula sit amet erat pharetra semper eget sit amet felis. Proin semper pellentesque dui sed consequat. Nam viverra nulla et ex consectetur mattis. Integer sed fermentum elit. Sed quam est, accumsan ac purus eget, lacinia venenatis augue. In scelerisque posuere quam sed suscipit. Nunc ac fringilla elit. Quisque eget sodales leo. Cras placerat laoreet tellus.</p>\r\n', 1, 'dfb557c2ed0d3e1ceb6935beaf.png', 1, '2020-08-02 20:04:11', 1, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `name` varchar(80) NOT NULL,
  `username` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password` varchar(200) NOT NULL,
  `profile` varchar(180) DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `activate` tinyint(1) NOT NULL,
  `twostep` tinyint(1) NOT NULL,
  `darkmode` tinyint(1) NOT NULL,
  `apikey` varchar(120) NOT NULL,
  `ban` tinyint(1) NOT NULL
) ;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `name`, `username`, `email`, `password`, `profile`, `date`, `activate`, `twostep`, `darkmode`, `apikey`, `ban`) VALUES
(1, 'ghi', 'ghi', 'ghi@gmail.com', '$2b$12$b./zCAbzs9XG0Dk8m/9Q5OTGmnMF.IFXdnfsTF55KwVtToDRnT0vi', '44dca6f897fac1b5b46a35a230.png', '2020-08-02 19:49:02', 1, 0, 0, 'f754685abf24508f746ff1e8bf5828a0c7', 0),
(2, 'jkl', 'jkl', 'jkl@gmail.com', '$2b$12$4iB56uF1upG8/Wwr8RV2P.BMlTkof.sZnzbGoo8oxbOyWmAZzLcXO', 'profile.jpg', '2020-08-02 19:49:03', 1, 0, 0, '227cc561331c830fbbc29fbaec3fccd0c6', 0);

-- --------------------------------------------------------

--
-- Table structure for table `user_to_admins`
--

CREATE TABLE `user_to_admins` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `subject` varchar(6000) NOT NULL,
  `message` varchar(6000) NOT NULL,
  `date` datetime DEFAULT NULL,
  `read` tinyint(1) NOT NULL
) ;

--
-- Dumping data for table `user_to_admins`
--

INSERT INTO `user_to_admins` (`id`, `user_id`, `subject`, `message`, `date`, `read`) VALUES
(1, 1, 'To All Admins', 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum nec feugiat turpis, non malesuada leo. Curabitur commodo arcu a vehicula tristique.', '2020-08-02 19:59:38', 0);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `apikey` (`apikey`);

--
-- Indexes for table `admincode`
--
ALTER TABLE `admincode`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code` (`code`);

--
-- Indexes for table `admin_to_all_users`
--
ALTER TABLE `admin_to_all_users`
  ADD PRIMARY KEY (`id`),
  ADD KEY `admin_id` (`admin_id`);

--
-- Indexes for table `admin_to_user`
--
ALTER TABLE `admin_to_user`
  ADD PRIMARY KEY (`id`),
  ADD KEY `admin_id` (`admin_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `authors`
--
ALTER TABLE `authors`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `blogpost`
--
ALTER TABLE `blogpost`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `title` (`title`),
  ADD UNIQUE KEY `slug` (`slug`),
  ADD KEY `category_id` (`category_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `bugreport`
--
ALTER TABLE `bugreport`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `category`
--
ALTER TABLE `category`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `contact`
--
ALTER TABLE `contact`
  ADD PRIMARY KEY (`sno`);

--
-- Indexes for table `posts`
--
ALTER TABLE `posts`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `title` (`title`),
  ADD UNIQUE KEY `slug` (`slug`),
  ADD KEY `category_id` (`category_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `apikey` (`apikey`);

--
-- Indexes for table `user_to_admins`
--
ALTER TABLE `user_to_admins`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `admincode`
--
ALTER TABLE `admincode`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `admin_to_all_users`
--
ALTER TABLE `admin_to_all_users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `admin_to_user`
--
ALTER TABLE `admin_to_user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `authors`
--
ALTER TABLE `authors`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `blogpost`
--
ALTER TABLE `blogpost`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `bugreport`
--
ALTER TABLE `bugreport`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `category`
--
ALTER TABLE `category`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `contact`
--
ALTER TABLE `contact`
  MODIFY `sno` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `posts`
--
ALTER TABLE `posts`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `user_to_admins`
--
ALTER TABLE `user_to_admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `admin_to_all_users`
--
ALTER TABLE `admin_to_all_users`
  ADD CONSTRAINT `admin_to_all_users_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `admin_to_user`
--
ALTER TABLE `admin_to_user`
  ADD CONSTRAINT `admin_to_user_ibfk_1` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `admin_to_user_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `blogpost`
--
ALTER TABLE `blogpost`
  ADD CONSTRAINT `blogpost_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `blogpost_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `authors` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `posts`
--
ALTER TABLE `posts`
  ADD CONSTRAINT `posts_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `posts_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `authors` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_to_admins`
--
ALTER TABLE `user_to_admins`
  ADD CONSTRAINT `user_to_admins_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
