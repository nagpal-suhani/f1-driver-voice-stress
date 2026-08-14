import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-40 h-14 flex items-center justify-between px-6 md:px-10 border-b border-white/5 backdrop-blur-sm bg-void/40"
    >
      <Link to="/" className="flex items-center gap-2.5">
        {/* <span className="w-2 h-2 bg-accent" /> */}
        <img
          src="https://www.theracefans.com/cdn/shop/files/2000222-CHARLES-LECLERC-2025-Mini-3.webp?v=1776007032&width=1946"
          alt="Logo"
          className="w-10 h-10 rounded-full"
        />
        <span className="font-display text-sm tracking-[0.3em] uppercase text-offwhite/90">
          Silent Co-Driver
        </span>
      </Link>
      <nav className="hidden md:flex items-center gap-8 label-micro text-muted/70">
        {/* Intentionally minimal — nav items to be decided later. */}
      </nav>
      <div className="label-micro text-muted/50">RACE ENGINEERING CONSOLE</div>
    </motion.header>
  );
}
