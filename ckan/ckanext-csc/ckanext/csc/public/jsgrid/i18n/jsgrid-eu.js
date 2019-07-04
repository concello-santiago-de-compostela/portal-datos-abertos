(function(jsGrid) {

    jsGrid.locales.eu = {
        grid: {
            noDataContent: "Ez da aurkitu",
            deleteConfirm: "Ziur zaude?",
            pagerFormat: "{first} {prev} {pages} {next} {last} &nbsp;&nbsp;&nbsp;&nbsp; Orria {pageIndex} tik {pageCount}",
            pagePrevText: "<",
            pageNextText: ">",
            pageFirstText: "<<",
            pageLastText: ">>",
            loadMessage: "Itxaron, mesedez...",
            invalidMessage: "Datu baliogabeak"
        },

        loadIndicator: {
            message: "Kargatzen..."
        },

        fields: {
            control: {
                searchModeButtonTooltip: "Aldatu bilaketara",
                insertModeButtonTooltip: "Aldatu txertatzera",
                editButtonTooltip: "Aldatu",
                deleteButtonTooltip: "Ezabatu",
                searchButtonTooltip: "Bilatu",
                clearFilterButtonTooltip: "Iragazkia kendu",
                insertButtonTooltip: "Txertatu",
                updateButtonTooltip: "Eguneratu",
                cancelEditButtonTooltip: "Utzi editatzeari"
            }
        },

        validators: {
            required: { message: "Beharrezko eremua" },
            rangeLength: { message: "Balioaren luzera zehaztutako tartetik kanpo dago" },
            minLength: { message: "Balioaren luzera motzegia da" },
            maxLength: { message: "Balioaren luzera luzeegia da" },
            pattern: { message: "Balioa ez dator bat zehaztutako ereduarekin" },
            range: { message: "Balioa zehaztutako barrutik kanpo dago" },
            min: { message: "Balioa txikiegia da" },
            max: { message: "Balioa handiegia da" }
        }
    };

}(jsGrid, jQuery));
