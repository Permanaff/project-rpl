-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 17 Bulan Mei 2024 pada 03.28
-- Versi server: 10.4.24-MariaDB
-- Versi PHP: 7.4.29

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `cinema`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `booking`
--

CREATE TABLE `booking` (
  `id_booking` varchar(15) NOT NULL,
  `id_user` varchar(11) NOT NULL,
  `id_schedule` varchar(10) NOT NULL,
  `id_drink` varchar(20) NOT NULL,
  `tanggal_booking` date NOT NULL,
  `jml_seat` tinyint(4) DEFAULT NULL,
  `total` int(25) NOT NULL,
  `qrcode` varchar(40) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` varchar(30) NOT NULL DEFAULT 'proses',
  `metode_bayar` varchar(20) DEFAULT NULL,
  `kode_bayar` varchar(80) DEFAULT NULL,
  `batas_bayar` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Struktur dari tabel `carousel`
--

CREATE TABLE `carousel` (
  `id_carousel` int(11) NOT NULL,
  `nama_carousel` varchar(50) NOT NULL,
  `image_carousel` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Struktur dari tabel `detail_booking`
--

CREATE TABLE `detail_booking` (
  `id_detail` int(11) NOT NULL,
  `id_booking` varchar(15) DEFAULT NULL,
  `no_seat` varchar(5) DEFAULT NULL,
  `id_seat` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Struktur dari tabel `drink`
--

CREATE TABLE `drink` (
  `id_drink` varchar(20) NOT NULL,
  `drink_name` varchar(30) NOT NULL,
  `image_drink` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Struktur dari tabel `movies`
--

CREATE TABLE `movies` (
  `id_movie` varchar(10) NOT NULL,
  `title` varchar(255) NOT NULL,
  `sinopsis` longtext NOT NULL,
  `sutradara` varchar(100) NOT NULL,
  `penulis` varchar(75) NOT NULL,
  `produser` varchar(75) NOT NULL,
  `produksi` varchar(75) NOT NULL,
  `cast` varchar(150) NOT NULL,
  `genre` varchar(20) NOT NULL,
  `durasi` tinyint(11) NOT NULL,
  `rating` enum('SU','13+','17+') NOT NULL,
  `tanggal_rilis` date DEFAULT NULL,
  `tahun` varchar(4) NOT NULL,
  `status` enum('aktif','non-aktif') DEFAULT 'aktif',
  `preorder` enum('ya','tidak') DEFAULT 'tidak',
  `tanggal_preorder` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Struktur dari tabel `poster_image`
--

CREATE TABLE `poster_image` (
  `id_poster` int(11) NOT NULL,
  `id_movie` varchar(10) NOT NULL,
  `poster_name` varchar(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Struktur dari tabel `schedule`
--

CREATE TABLE `schedule` (
  `id_schedule` varchar(10) NOT NULL,
  `id_movie` varchar(10) NOT NULL,
  `id_theaters` varchar(10) NOT NULL,
  `tanggal_schedule` date NOT NULL,
  `jam` varchar(5) NOT NULL,
  `studio` enum('1','2','3') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Struktur dari tabel `theaters`
--

CREATE TABLE `theaters` (
  `id_theaters` varchar(10) NOT NULL,
  `nama_theaters` varchar(45) NOT NULL,
  `alamat_theaters` varchar(120) NOT NULL,
  `no_telp` varchar(15) DEFAULT NULL,
  `price1` enum('25000','30000') NOT NULL,
  `price2` enum('30000','35000') NOT NULL,
  `price3` enum('35000','40000') NOT NULL,
  `region` enum('36','32','33','35','60','19') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Struktur dari tabel `users`
--

CREATE TABLE `users` (
  `id_user` varchar(11) NOT NULL,
  `nama` varchar(75) NOT NULL,
  `username` varchar(75) NOT NULL,
  `email` varchar(75) NOT NULL,
  `tanggal_lahir` date NOT NULL,
  `no_telp` varchar(15) DEFAULT NULL,
  `gender` enum('Pria','Wanita') DEFAULT NULL,
  `provinsi` int(11) DEFAULT NULL,
  `password` varchar(100) DEFAULT NULL,
  `pin` int(6) DEFAULT NULL,
  `alamat` varchar(100) DEFAULT NULL,
  `level_user` enum('1','2','3') DEFAULT '3',
  `id_theaters` varchar(10) DEFAULT NULL,
  `profile_image` varchar(100) DEFAULT 'avatar.jpg'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `booking`
--
ALTER TABLE `booking`
  ADD PRIMARY KEY (`id_booking`),
  ADD KEY `id_user` (`id_user`) USING BTREE,
  ADD KEY `id_schedule` (`id_schedule`),
  ADD KEY `id_drink` (`id_drink`);

--
-- Indeks untuk tabel `carousel`
--
ALTER TABLE `carousel`
  ADD PRIMARY KEY (`id_carousel`);

--
-- Indeks untuk tabel `detail_booking`
--
ALTER TABLE `detail_booking`
  ADD PRIMARY KEY (`id_detail`),
  ADD KEY `id_booking` (`id_booking`) USING BTREE;

--
-- Indeks untuk tabel `drink`
--
ALTER TABLE `drink`
  ADD PRIMARY KEY (`id_drink`);

--
-- Indeks untuk tabel `movies`
--
ALTER TABLE `movies`
  ADD PRIMARY KEY (`id_movie`);

--
-- Indeks untuk tabel `poster_image`
--
ALTER TABLE `poster_image`
  ADD PRIMARY KEY (`id_poster`),
  ADD UNIQUE KEY `id_movie` (`id_movie`);

--
-- Indeks untuk tabel `schedule`
--
ALTER TABLE `schedule`
  ADD PRIMARY KEY (`id_schedule`),
  ADD KEY `id_film` (`id_movie`) USING BTREE,
  ADD KEY `id_theaters` (`id_theaters`) USING BTREE;

--
-- Indeks untuk tabel `theaters`
--
ALTER TABLE `theaters`
  ADD PRIMARY KEY (`id_theaters`);

--
-- Indeks untuk tabel `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id_user`),
  ADD KEY `id_theaters` (`id_theaters`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `carousel`
--
ALTER TABLE `carousel`
  MODIFY `id_carousel` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `detail_booking`
--
ALTER TABLE `detail_booking`
  MODIFY `id_detail` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `poster_image`
--
ALTER TABLE `poster_image`
  MODIFY `id_poster` int(11) NOT NULL AUTO_INCREMENT;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `booking`
--
ALTER TABLE `booking`
  ADD CONSTRAINT `booking_ibfk_1` FOREIGN KEY (`id_user`) REFERENCES `users` (`id_user`),
  ADD CONSTRAINT `booking_ibfk_2` FOREIGN KEY (`id_drink`) REFERENCES `drink` (`id_drink`),
  ADD CONSTRAINT `booking_ibfk_3` FOREIGN KEY (`id_schedule`) REFERENCES `schedule` (`id_schedule`);

--
-- Ketidakleluasaan untuk tabel `detail_booking`
--
ALTER TABLE `detail_booking`
  ADD CONSTRAINT `detail_booking_ibfk_1` FOREIGN KEY (`id_booking`) REFERENCES `booking` (`id_booking`);

--
-- Ketidakleluasaan untuk tabel `poster_image`
--
ALTER TABLE `poster_image`
  ADD CONSTRAINT `poster_image_ibfk_1` FOREIGN KEY (`id_movie`) REFERENCES `movies` (`id_movie`);

--
-- Ketidakleluasaan untuk tabel `schedule`
--
ALTER TABLE `schedule`
  ADD CONSTRAINT `schedule_ibfk_1` FOREIGN KEY (`id_movie`) REFERENCES `movies` (`id_movie`),
  ADD CONSTRAINT `schedule_ibfk_2` FOREIGN KEY (`id_theaters`) REFERENCES `theaters` (`id_theaters`);

--
-- Ketidakleluasaan untuk tabel `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`id_theaters`) REFERENCES `theaters` (`id_theaters`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
