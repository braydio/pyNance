<!-- Deprecated component: retained only for historical reference -->
<template>
    <div class="video-container">
      <!-- The YouTube player will be embedded in this div -->
      <div id="player"></div>
      <button @click="toggleMute" class="mute-toggle">
        {{ isMuted ? "Unmute" : "Mute" }}
      </button>
    </div>
  </template>
  
  <script>
  export default {
    name: "YouTubePlayer",
    data() {
      return {
        player: null,
        isMuted: false, // start unmuted
      };
    },
    methods: {
      onYouTubeIframeAPIReady() {
        this.player = new window.YT.Player('player', {
          height: '315',
          width: '560',
          videoId: 'YOUR_VIDEO_ID', // Replace with your actual video ID
          playerVars: {
            autoplay: 1,
            mute: 0,         // Set mute to 0 so it loads unmuted
            controls: 1,
          },
          events: {
            'onReady': this.onPlayerReady,
          },
        });
      },
      onPlayerReady(event) {
        // Ensure the video is unmuted, then play.
        event.target.unMute();
        event.target.playVideo();
      },
      toggleMute() {
        if (this.player) {
          if (this.isMuted) {
            this.player.unMute();
            this.isMuted = false;
          } else {
            this.player.mute();
            this.isMuted = true;
          }
        }
      },
      loadYouTubeAPI() {
        // If the API is already loaded, call the ready function
        if (window.YT && window.YT.Player) {
          this.onYouTubeIframeAPIReady();
        } else {
          const tag = document.createElement('script');
          tag.src ="https://www.youtube.com/embed/YOUR_VIDEO_ID?autoplay=1&mute=1";
          const firstScriptTag = document.getElementsByTagName('script')[0];
          firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
          // Assign our method to the global callback
          window.onYouTubeIframeAPIReady = this.onYouTubeIframeAPIReady;
        }
      },
    },
    mounted() {
      this.loadYouTubeAPI();
    },
  };
  </script>
  
  <style scoped>
@reference "../../assets/css/main.css";
@reference '@/styles/global-colors.css';

  .video-container {
    position: relative;
    padding-bottom: 56.25%; /* 16:9 aspect ratio */
    padding-top: 25px;
    height: 0;
    width: 100%;
    margin-bottom: 1rem;
  }
  #player {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }
  .mute-toggle {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background-color: var(--gruvbox-accent);
    color: var(--gruvbox-fg);
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  .mute-toggle:hover {
    background-color: var(--gruvbox-hover);
  }
  
</style>
  