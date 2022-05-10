function saveFingerprint(width, height, context, url) {
    if (width < 16 || height < 16) {
        return;
    };

    if (10 > String.prototype.concat(...new Set(context.writenText)).length &&
        2 > [...new Set(context.usedFillStyles)].length) {
        return;
    };

    if (context.calledForbiddenFunction == true) {
        return;
    };

    var img = document.createElement('img');
    img.src = url;
    img.callee = JSON.stringify(document.currentScript);
    img.classList.add('canvas_img_crawler');
    document.body.appendChild(img);
};

document.defaultView.HTMLCanvasElement.prototype.toDataURL_original = document.defaultView.HTMLCanvasElement.prototype.toDataURL;
document.defaultView.HTMLCanvasElement.prototype.toDataURL = function () {
    const url = this.toDataURL_original(...arguments);
    var context = this.getContext('2d');
    saveFingerprint(this.width, this.height, context, url);
    return url;
};

document.defaultView.HTMLCanvasElement.prototype.getContext_original = document.defaultView.HTMLCanvasElement.prototype.getContext;
document.defaultView.HTMLCanvasElement.prototype.getContext = function () {
    var context = this.getContext_original(...arguments);

    context.saveWrittenText = function (text) {
        if (this.writenText == undefined) {
            this.writenText = text;
        } else {
            this.writenText += text;
        }
    };

    context.saveFillStyle = function () {
        if (this.usedFillStyles == undefined) {
            this.usedFillStyles = [JSON.stringify(this.fillStyle)];
        } else {
            this.usedFillStyles.push(JSON.stringify(this.fillStyle));
        }
    };

    context.fillText_original = context.fillText;
    context.fillText = function() {
        this.saveWrittenText(arguments[0]);
        this.saveFillStyle();
        return this.fillText_original(...arguments);
    };

    context.strokeText_original = context.strokeText;
    context.strokeText = function() {
        this.saveWrittenText(arguments[0]);
        this.saveFillStyle();
        return this.strokeText_original(...arguments);
    };

    context.save_original = context.save;
    context.save = function() {
        this.calledForbiddenFunction = true;
        return this.save_original(...arguments);
    };

    context.restore_original = context.restore;
    context.restore = function() {
        this.calledForbiddenFunction = true;
        return this.restore_original(...arguments);
    };

    context.getImageData_original = context.getImageData;
    context.getImageData = function() {
        const img = this.getImageData_original(...arguments);
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        ctx.writtenText = this.writtenText;
        ctx.usedFillStyles = this.usedFillStyles;
        ctx.calledForbiddenFunction = this.calledForbiddenFunction;
        ctx.putImageData(img, 0, 0);
        canvas.toDataURL();
        return img;
    };

    return context;
};
