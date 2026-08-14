import Navbar from "../components/common/Navbar";
import { HeroBackground, HeroContent } from "../components/landing/Hero";
import SetupForm from "../components/landing/SetupForm";

export default function Home() {
  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      <Navbar />
      <main className="relative min-h-screen flex items-center px-6 md:px-12 lg:px-20 pt-14">
        <HeroBackground />
        <div className="w-full flex flex-col lg:flex-row items-center justify-between gap-14 py-16">
          <HeroContent />
          <div className="shrink-0">
            <SetupForm />
          </div>
        </div>
      </main>
    </div>
  );
}
