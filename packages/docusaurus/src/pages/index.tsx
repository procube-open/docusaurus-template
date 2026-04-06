import { useEffect } from "react"
import clsx from "clsx"
import useDocusaurusContext from "@docusaurus/useDocusaurusContext"
import Layout from "@theme/Layout"
import Heading from "@theme/Heading"

import styles from "./index.module.css"

const descriptionSection = (
    <div id="hero" className={styles.heroSection}>
        <canvas id="hero-canvas" className={styles.heroCanvas}></canvas>
        <div className={styles.heroContent}>
            <h1 className={styles.heroTitle}>分散マイクロサービス基盤</h1>
            <p className={styles.heroSubtitle}>
                オンデマンドでマイクロサービスを<b>持ち寄り</b>、強固で巨大なシステムを構築する
            </p>
        </div>
    </div>
)

function animateChipin() {
    const canvas = document.getElementById("hero-canvas") as HTMLCanvasElement
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let width: number, height: number, nodes: any[], center: { x: number; y: number }

    const icons = {
        cloud: "☁️",
        laptop: "💻",
        coffee: "☕",
        server: "🗄️",
        mobile: "📱",
    }

    function init() {
        width = canvas.width = canvas.offsetWidth
        height = canvas.height = canvas.offsetHeight
        center = { x: width / 2, y: height / 2 }

        nodes = [
            {
                x: 0,
                y: 0,
                icon: icons.cloud,
                size: 35,
                angle: Math.random() * 2 * Math.PI,
                radius: Math.min(width, height) * 0.3,
            },
            {
                x: 0,
                y: 0,
                icon: icons.laptop,
                size: 25,
                angle: Math.random() * 2 * Math.PI,
                radius: Math.min(width, height) * 0.22,
            },
            {
                x: 0,
                y: 0,
                icon: icons.coffee,
                size: 25,
                angle: Math.random() * 2 * Math.PI,
                radius: Math.min(width, height) * 0.26,
            },
            {
                x: 0,
                y: 0,
                icon: icons.server,
                size: 30,
                angle: Math.random() * 2 * Math.PI,
                radius: Math.min(width, height) * 0.18,
            },
            {
                x: 0,
                y: 0,
                icon: icons.mobile,
                size: 20,
                angle: Math.random() * 2 * Math.PI,
                radius: Math.min(width, height) * 0.15,
            },
        ]

        animate()
    }

    function animate() {
        ctx.clearRect(0, 0, width, height)

        ctx.fillStyle = "rgba(0, 0, 0, 0.4)"
        ctx.fillRect(0, 0, width, height)

        nodes.forEach((node) => {
            node.angle += 0.001
            node.x = center.x + node.radius * Math.cos(node.angle)
            node.y = center.y + node.radius * Math.sin(node.angle)
        })

        nodes.forEach((node) => {
            nodes.forEach((otherNode) => {
                if (node !== otherNode) {
                    ctx.beginPath()
                    ctx.moveTo(node.x, node.y)
                    ctx.lineTo(otherNode.x, otherNode.y)
                    ctx.strokeStyle = "rgba(255, 255, 255, 0.1)"
                    ctx.stroke()
                }
            })
        })

        ctx.beginPath()
        ctx.arc(center.x, center.y, 25, 0, 2 * Math.PI)
        ctx.fillStyle = "rgba(59, 130, 246, 0.8)"
        ctx.fill()
        ctx.font = "20px sans-serif"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        ctx.fillStyle = "#fff"
        ctx.fillText("🌐", center.x, center.y)

        nodes.forEach((node) => {
            ctx.beginPath()
            ctx.moveTo(node.x, node.y)
            ctx.lineTo(center.x, center.y)
            ctx.strokeStyle = "rgba(255, 255, 255, 0.3)"
            ctx.stroke()

            ctx.font = `${node.size}px sans-serif`
            ctx.textAlign = "center"
            ctx.textBaseline = "middle"
            ctx.fillText(node.icon, node.x, node.y)
        })

        requestAnimationFrame(animate)
    }

    const handleResize = () => init()
    window.addEventListener("resize", handleResize)
    init()

    // クリーンアップ関数を返す
    return () => {
        window.removeEventListener("resize", handleResize)
    }
}

function HomepageHeader() {
    const { siteConfig } = useDocusaurusContext()
    const HeadingComponent = Heading as any
    return (
        <header className={clsx("hero hero--primary", styles.heroBanner)}>
            <div className="container">
                <HeadingComponent as="h1" className="hero__title">
                    {siteConfig.title}
                </HeadingComponent>
                <p className="hero__subtitle">開発者ポータル</p>
            </div>
        </header>
    )
}

export default function Home(): React.JSX.Element {
    const { siteConfig } = useDocusaurusContext()
    const LayoutComponent = Layout as any

    // useEffectでアニメーションを開始
    useEffect(() => {
        const cleanup = animateChipin()
        return cleanup
    }, [])

    return (
        <LayoutComponent title={`${siteConfig.title}`} description="Description will go into a meta tag in <head />">
            <HomepageHeader />
            <main>
                {descriptionSection}
            </main>
        </LayoutComponent>
    )
}
