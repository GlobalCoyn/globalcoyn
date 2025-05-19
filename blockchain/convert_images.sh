#!/bin/bash
# Script to convert SVG diagrams to PNG for the website

echo "Converting network diagram to PNG..."
mkdir -p blockchain/website/assets

# Check if we have the ability to convert images
if command -v convert &> /dev/null; then
    echo "Using ImageMagick to convert SVGs to PNGs..."
    
    # Using ImageMagick if available
    convert -background none -size 800x400 blockchain/website/assets/network-diagram.svg blockchain/website/assets/network-diagram.png
    
    # Create a blockchain diagram
    convert -size 800x400 xc:'#F6F9FC' -fill '#3461FF' -draw 'roundrectangle 50,50,750,350,10,10' blockchain/website/assets/temp.png
    
    # Add blocks
    for i in {1..6}; do
        x=$((100 + i*100))
        convert blockchain/website/assets/temp.png -fill '#05B169' -draw "rectangle $x,100,$((x+80)),300" blockchain/website/assets/temp.png
    done
    
    # Add connections
    for i in {1..5}; do
        x1=$((180 + i*100))
        x2=$((200 + i*100))
        convert blockchain/website/assets/temp.png -stroke '#FFB830' -strokewidth 4 -draw "line $x1,200 $x2,200" blockchain/website/assets/temp.png
    done
    
    # Finalize the image
    convert blockchain/website/assets/temp.png -font Arial -pointsize 20 -fill white -annotate +350+200 'GlobalCoyn Blockchain' blockchain/website/assets/blockchain-illustration.png
    
    # Clean up
    rm blockchain/website/assets/temp.png
    
    echo "PNG images created successfully."
else
    echo "ImageMagick not available. Creating simple placeholder images instead..."
    
    # Create simple placeholder HTML files that look like images
    cat > blockchain/website/assets/network-diagram.png.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Network Diagram</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }
        .diagram {
            width: 800px;
            height: 400px;
            background-color: #F6F9FC;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #3461FF;
        }
        .content {
            display: flex;
            justify-content: space-between;
            width: 80%;
        }
        .node {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-weight: bold;
        }
        .bootstrap {
            background-color: #3461FF;
        }
        .regular {
            background-color: #05B169;
        }
        .new {
            background-color: #FFB830;
        }
        .line {
            width: 100%;
            height: 2px;
            background-color: #3461FF;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="diagram">
        <div class="title">GlobalCoyn Network Infrastructure</div>
        <div class="content">
            <div class="node bootstrap">B1</div>
            <div class="node regular">N1</div>
            <div class="node regular">N2</div>
            <div class="node new">New</div>
            <div class="node bootstrap">B2</div>
        </div>
        <div class="line"></div>
        <p>Decentralized network with bootstrap nodes and peer connections</p>
    </div>
</body>
</html>
EOL

    cat > blockchain/website/assets/blockchain-illustration.png.html << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Blockchain Illustration</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }
        .diagram {
            width: 800px;
            height: 400px;
            background-color: #F6F9FC;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #3461FF;
        }
        .blocks {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
        .block {
            width: 80px;
            height: 100px;
            background-color: #05B169;
            margin: 0 10px;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-weight: bold;
        }
        .chain {
            height: 4px;
            background-color: #FFB830;
            width: 30px;
            margin: 0 -5px;
        }
    </style>
</head>
<body>
    <div class="diagram">
        <div class="title">GlobalCoyn Blockchain</div>
        <div class="blocks">
            <div class="block">Block 1</div>
            <div class="chain"></div>
            <div class="block">Block 2</div>
            <div class="chain"></div>
            <div class="block">Block 3</div>
            <div class="chain"></div>
            <div class="block">Block 4</div>
        </div>
        <p>GlobalCoyn's transparent and secure blockchain</p>
    </div>
</body>
</html>
EOL

    # Rename the files
    mv blockchain/website/assets/network-diagram.png.html blockchain/website/assets/network-diagram.png
    mv blockchain/website/assets/blockchain-illustration.png.html blockchain/website/assets/blockchain-illustration.png
    
    echo "HTML placeholders created. Replace with actual images when possible."
fi

echo "Done preparing images."