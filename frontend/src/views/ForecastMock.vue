<template>
  <div class="min-h-screen w-full bg-[#0a0a12] text-neutral-100 flex flex-col relative font-outfit">
    <!-- Header/Nav -->
    <header
      class="w-full bg-black flex flex-col items-start px-20 py-16 border-b border-gray-800 shadow-lg relative overflow-visible">
      <!-- Invisible TSU STU header -->
      <div class="absolute left-1/2 -translate-x-1/2 top-6 z-0 select-none pointer-events-none" style="color: #0a0a12;">
      </div>
      <!-- Main studio name, foreground -->
      <div class="relative z-10 text-5xl font-serif tracking-[0.32em] font-bold select-none">
        TSUEHARA STUDIO
      </div>
    </header>

    <main class="flex flex-col flex-1 items-center justify-center px-10">
      <!-- Artistic Message Row -->
      <div class="flex flex-row w-full max-w-[1400px] justify-center items-start gap-28 mt-20">
        <div class="flex flex-col items-start max-w-xs min-w-[260px]">
          <p
            class="font-outfit font-semibold uppercase tracking-widest leading-relaxed text-[1.07rem] text-neutral-200 drop-shadow">
            <span class="text-accent-400 font-bold italic">VISUAL LANGUAGE</span>
            <span class="text-emerald-300/90 font-semibold"> IS</span><br>
            THE ATMOSPHERE THAT<br>
            ENTICES <span class="text-amber-300">ONLOOKERS</span>,<br>
            <span class="italic text-sky-300/90">PERMEATING</span><br>
            THEIR SENSES.<br>
            TO SAY SOMETHING<br>
            <span class="text-cyan-300/70 font-medium">WITHOUT WORDS</span> IS THE<br>
            PULSE OF ANY BRAND<br>
            OR <span class="text-amber-300 font-semibold">ARTIST’S VISION</span>.
          </p>
        </div>
        <div class="flex flex-col items-center max-w-xs min-w-[260px]">
          <p
            class="font-outfit font-semibold uppercase tracking-widest leading-relaxed text-[1.07rem] text-center text-neutral-200 drop-shadow">
            IN THIS <span class="italic text-sky-400/90">LIMINAL WORLD</span>,<br>
            <span class="text-accent-300">CONCEPTS</span> ARE<br>
            CREATED LESS<br>
            LIKE A <span class="italic text-amber-200">CHOIR</span> AND MORE<br>
            LIKE A <span class="font-semibold text-emerald-300">SYMPHONY</span>.
          </p>
        </div>
        <div class="flex flex-col items-center max-w-xs min-w-[260px]">
          <p
            class="font-outfit font-semibold uppercase tracking-widest leading-relaxed text-[1.07rem] text-center text-neutral-200 drop-shadow">
            THE FOUNDATION FOR<br>
            THIS <span class="text-accent-400">COLLABORATION</span><br>
            STARTS WITH<br>
            <span class="font-black text-amber-300 text-[1.18rem]">TSUEHARA STUDIO.</span>
          </p>
        </div>
      </div>

      <!-- Button row: three columns, only middle and right have buttons -->
      <div class="flex flex-row w-full max-w-[1400px] justify-center mt-16 gap-28">
        <div class="flex flex-col max-w-xs min-w-[260px]"></div>
        <div class="flex flex-col max-w-xs min-w-[260px] pl-4">
          <button class="art-cta-btn self-start">Studio Overview</button>
        </div>
        <div class="flex flex-col max-w-xs min-w-[260px] pr-4">
          <button class="art-cta-btn self-end">Featured Prints</button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;900&display=swap');

.font-outfit {
  font-family: 'Outfit', 'Montserrat', 'Arial', sans-serif;
}

.art-cta-btn {
  width: auto;
  min-width: 132px;
  padding: 0.6rem 2rem;
  border-radius: 9999px;
  border: 2px solid #36e0e5;
  background: rgba(26, 36, 37, 0.17);
  color: #e0f8fa;
  text-transform: uppercase;
  font-size: 0.99rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  box-shadow: 0 1.5px 8px 0 rgba(22, 188, 217, 0.13);
  transition:
    background 0.22s cubic-bezier(.4, 2, .7, .9),
    color 0.15s,
    border-color 0.17s,
    box-shadow 0.17s;
  outline: none;
  backdrop-filter: blur(1.5px);
}

.art-cta-btn:hover,
.art-cta-btn:focus {
  background: rgba(58, 225, 255, 0.18);
  color: #131312;
  border-color: #ffe181;
  box-shadow: 0 6px 32px 2px rgba(58, 225, 255, 0.12);
  cursor: pointer;
}
</style>
