import Lenis from '@studio-freight/lenis'
import gsap from 'gsap'
import ScrollTrigger from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// ============================================================
//  SMOOTH SCROLL (LENIS)
// ============================================================
const lenis = new Lenis({
    lerp: 0.07,
    smoothWheel: true,
    syncTouch: false,
    gestureOrientation: 'vertical',
    touchMultiplier: 1.5,
    infinite: false,
})

lenis.on('scroll', ScrollTrigger.update)

gsap.ticker.add((time) => {
    lenis.raf(time * 1000)
})
gsap.ticker.lagSmoothing(0)

// ============================================================
//  PRELOADER — dismiss on load or after 2s timeout (whichever first)
// ============================================================
let heroDone = false

function dismissPreloader() {
    if (heroDone) return
    heroDone = true
    const preloader = document.getElementById('preloader')
    if (preloader) {
        setTimeout(() => {
            preloader.classList.add('loaded')
            setTimeout(runHeroIntro, 300)
        }, 1400)
    } else {
        runHeroIntro()
    }
}

// Fires when images/fonts all loaded
window.addEventListener('load', dismissPreloader)
// Fallback: fire after 2.5s no matter what (handles file:// protocol edge cases)
setTimeout(dismissPreloader, 2500)
// Even earlier fallback
document.addEventListener('DOMContentLoaded', () => setTimeout(dismissPreloader, 2000))

// ============================================================
//  HERO CINEMATIC INTRO
// ============================================================
function runHeroIntro() {
    const tl = gsap.timeline({ defaults: { ease: 'power4.out' } })

    // Nav
    tl.fromTo('.premium-nav',
        { opacity: 0, y: -20 },
        { opacity: 1, y: 0, duration: 1 },
        0
    )

    // Image zoom in
    tl.fromTo('#heroImg',
        { scale: 1.2, filter: 'brightness(0) contrast(110%)' },
        { scale: 1, filter: 'contrast(110%) brightness(0.65)', duration: 2.8, ease: 'power3.inOut' },
        0
    )

    // Architectural lines
    tl.fromTo('.hero-line.left',
        { scaleY: 0, transformOrigin: 'top' },
        { scaleY: 1, duration: 1.8, ease: 'power3.out' },
        0.3
    )
    tl.fromTo('.hero-line.right',
        { scaleY: 0, transformOrigin: 'bottom' },
        { scaleY: 1, duration: 1.8, ease: 'power3.out' },
        0.5
    )
    tl.fromTo('.hero-line.bottom',
        { scaleX: 0, transformOrigin: 'left' },
        { scaleX: 1, duration: 1.2, ease: 'power3.out' },
        0.8
    )

    // Text reveals (staggered)
    tl.fromTo('.reveal-text',
        { y: 60, skewY: 4, opacity: 0 },
        { y: 0, skewY: 0, opacity: 1, duration: 1.4, stagger: 0.12, ease: 'power3.out' },
        0.8
    )

    // Form and scroll indicators
    tl.fromTo(['#heroForm', '#scrollIndicator', '.hero-corner-tag'],
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 1, stagger: 0.15 },
        1.4
    )
}

// ============================================================
//  NAV — SCROLL STATE
// ============================================================
const nav = document.getElementById('nav')
if (nav) {
    ScrollTrigger.create({
        start: 'top -60',
        onUpdate: (self) => {
            if (self.scroller.scrollTop > 60 || self.progress > 0) {
                nav.classList.add('scrolled')
            } else {
                nav.classList.remove('scrolled')
            }
        }
    })

    // Simpler approach using scroll listener via lenis
    lenis.on('scroll', ({ scroll }) => {
        if (scroll > 60) {
            nav.classList.add('scrolled')
        } else {
            nav.classList.remove('scrolled')
        }
    })
}

// ============================================================
//  FADE-UP ELEMENTS (IntersectionObserver — no GSAP overhead)
// ============================================================
const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible')
            fadeObserver.unobserve(entry.target)
        }
    })
}, { threshold: 0.12, rootMargin: '0px 0px -50px 0px' })

document.querySelectorAll('.fade-up').forEach(el => fadeObserver.observe(el))

// ============================================================
//  IMAGE REVEAL MASKS (GSAP clip-path)
// ============================================================
document.querySelectorAll('.reveal-mask').forEach(wrap => {
    gsap.fromTo(wrap,
        { clipPath: 'inset(100% 0 0 0)' },
        {
            clipPath: 'inset(0% 0 0 0)',
            duration: 1.6,
            ease: 'expo.inOut',
            scrollTrigger: {
                trigger: wrap,
                start: 'top 82%',
            }
        }
    )

    // Parallax on inner image
    const img = wrap.querySelector('img')
    const speed = parseFloat(wrap.dataset.speed) || 1
    if (img && speed !== 1) {
        gsap.to(img, {
            yPercent: (speed - 1) * 100 * 0.4,
            ease: 'none',
            scrollTrigger: {
                trigger: wrap,
                start: 'top bottom',
                end: 'bottom top',
                scrub: true
            }
        })
    }
})

// ============================================================
//  HERO IMAGE PARALLAX
// ============================================================
gsap.to('#heroBg', {
    yPercent: 15,
    ease: 'none',
    scrollTrigger: {
        trigger: '.hero-section',
        start: 'top top',
        end: 'bottom top',
        scrub: true
    }
})

// ============================================================
//  CTA BACKGROUND PARALLAX
// ============================================================
gsap.to('#ctaBg', {
    yPercent: 12,
    ease: 'none',
    scrollTrigger: {
        trigger: '.cta-section',
        start: 'top bottom',
        end: 'bottom top',
        scrub: true
    }
})

// ============================================================
//  ANIMATED COUNTERS
// ============================================================
const counters = document.querySelectorAll('.counter')
let countersAnimated = false

ScrollTrigger.create({
    trigger: '#counters',
    start: 'top 80%',
    onEnter: () => {
        if (countersAnimated) return
        countersAnimated = true

        counters.forEach(counter => {
            const target = +counter.getAttribute('data-target')
            gsap.to(counter, {
                innerHTML: target,
                duration: target > 100 ? 2.5 : 1.8,
                snap: { innerHTML: 1 },
                ease: 'power2.out'
            })
        })
    }
})

// ============================================================
//  GALLERY — SHOW MORE + LIGHTBOX
// ============================================================
const loadMoreBtn = document.getElementById('loadMoreGallery')
const hiddenItems = document.querySelectorAll('.hidden-gallery')

if (loadMoreBtn && hiddenItems.length > 0) {
    loadMoreBtn.addEventListener('click', () => {
        hiddenItems.forEach((item, i) => {
            item.style.display = 'block'
            gsap.fromTo(item,
                { opacity: 0, y: 30 },
                { opacity: 1, y: 0, duration: 0.7, delay: i * 0.08, ease: 'power2.out' }
            )
        })
        loadMoreBtn.closest('.text-center').style.display = 'none'
        ScrollTrigger.refresh()
    })
}

// Lightbox
const lightbox = document.getElementById('lightbox')
const lightboxImg = document.getElementById('lightbox-img')
const lightboxClose = document.getElementById('lightboxClose')
const lightboxPrev = document.getElementById('lightboxPrev')
const lightboxNext = document.getElementById('lightboxNext')

let galleryImages = []
let currentLightboxIndex = 0

function buildGalleryImages() {
    galleryImages = []
    document.querySelectorAll('.lightbox-trigger').forEach((item) => {
        const src = item.getAttribute('data-src') || item.querySelector('img')?.src
        const alt = item.querySelector('img')?.alt || ''
        if (src) galleryImages.push({ src, alt })
    })
}

function openLightbox(index) {
    if (!lightbox || !lightboxImg) return
    currentLightboxIndex = index
    lightboxImg.src = galleryImages[index].src
    lightboxImg.alt = galleryImages[index].alt
    lightbox.classList.add('active')
    lenis.stop()
    document.body.style.overflow = 'hidden'
}

function closeLightbox() {
    if (!lightbox) return
    lightbox.classList.remove('active')
    lenis.start()
    document.body.style.overflow = ''
    setTimeout(() => { if (lightboxImg) lightboxImg.src = '' }, 400)
}

function showLightboxImage(index) {
    if (!galleryImages.length) return
    currentLightboxIndex = (index + galleryImages.length) % galleryImages.length
    if (lightboxImg) {
        gsap.to(lightboxImg, {
            opacity: 0, scale: 0.95, duration: 0.2,
            onComplete: () => {
                lightboxImg.src = galleryImages[currentLightboxIndex].src
                lightboxImg.alt = galleryImages[currentLightboxIndex].alt
                gsap.to(lightboxImg, { opacity: 1, scale: 1, duration: 0.3 })
            }
        })
    }
}

if (lightbox) {
    buildGalleryImages()

    document.querySelectorAll('.lightbox-trigger').forEach((item, index) => {
        item.addEventListener('click', () => openLightbox(index))
    })

    lightboxClose?.addEventListener('click', closeLightbox)
    lightboxPrev?.addEventListener('click', () => showLightboxImage(currentLightboxIndex - 1))
    lightboxNext?.addEventListener('click', () => showLightboxImage(currentLightboxIndex + 1))

    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox()
    })

    // Keyboard nav
    document.addEventListener('keydown', (e) => {
        if (!lightbox.classList.contains('active')) return
        if (e.key === 'Escape') closeLightbox()
        if (e.key === 'ArrowLeft') showLightboxImage(currentLightboxIndex - 1)
        if (e.key === 'ArrowRight') showLightboxImage(currentLightboxIndex + 1)
    })
}

// ============================================================
//  SMOOTH ANCHOR LINKS
// ============================================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href')
        if (targetId && targetId !== '#') {
            const targetEl = document.querySelector(targetId)
            if (targetEl) {
                e.preventDefault()
                lenis.scrollTo(targetEl, { offset: -80, duration: 1.4 })
            }
        }
    })
})

// ============================================================
//  ADV CARDS — NUMBER HOVER EFFECT
// ============================================================
document.querySelectorAll('.adv-card').forEach((card, i) => {
    card.addEventListener('mouseenter', () => {
        gsap.to(card.querySelector('.adv-icon-wrap'), {
            rotation: 5, scale: 1.05, duration: 0.4, ease: 'power2.out'
        })
    })
    card.addEventListener('mouseleave', () => {
        gsap.to(card.querySelector('.adv-icon-wrap'), {
            rotation: 0, scale: 1, duration: 0.4, ease: 'power2.out'
        })
    })
})

// ============================================================
//  PLAN CARDS — GSAP hover enhancement
// ============================================================
document.querySelectorAll('.plan-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
        gsap.to(card, { y: -8, duration: 0.4, ease: 'power2.out' })
    })
    card.addEventListener('mouseleave', () => {
        gsap.to(card, { y: 0, duration: 0.4, ease: 'power2.out' })
    })
})

// ============================================================
//  NUMBERS SECTION — STAGGER ANIMATION WHEN VISIBLE
// ============================================================
const numberItems = document.querySelectorAll('.number-item')
if (numberItems.length) {
    ScrollTrigger.create({
        trigger: '#numbers',
        start: 'top 75%',
        onEnter: () => {
            gsap.fromTo(numberItems,
                { opacity: 0, y: 30 },
                { opacity: 1, y: 0, duration: 0.8, stagger: 0.12, ease: 'power3.out' }
            )
        }
    })
}
